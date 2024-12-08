#include <stdio.h>
#include <string.h>
#include "driver/ledc.h"
#include "esp_err.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "dht.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "nvs_flash.h"
#include "esp_websocket_client.h"
#include "esp_system.h"
#include "cJSON.h"
#include "esp_pthread.h"

// LED Config for status indication
#define LED_PIN 15

// Servo Configuration
#define LEDC_TIMER              LEDC_TIMER_0
#define LEDC_MODE               LEDC_LOW_SPEED_MODE
#define LEDC_OUTPUT_IO          (5) // Servo GPIO pin
#define LEDC_CHANNEL            LEDC_CHANNEL_0
#define LEDC_DUTY_RES           LEDC_TIMER_14_BIT
#define LEDC_FREQUENCY          (50)
#define SERVO_MIN_PULSEWIDTH_US 500
#define SERVO_MAX_PULSEWIDTH_US 2500
#define SERVO_MAX_DEGREE        180

// Garage Configuration
#define SERVO_OPEN_ANGLE        170
#define SERVO_CLOSED_ANGLE      50
#define SERVO_STEP_DELAY_MS     50
#define UPDATE_INTERVAL_MS      5000

// Default WiFi and WebSocket configuration
#define DEFAULT_WIFI_SSID       "SEPIFANSEV"
#define DEFAULT_WIFI_PASS       "89262027736"
#define DEFAULT_WS_URI         "ws://192.168.96.181:8000/ws"

typedef enum {
    GARAGE_CLOSED,
    GARAGE_OPEN,
    GARAGE_MOVING
} garage_state_t;

typedef enum {
    LED_OFF,
    LED_ON,
    LED_BLINK_SLOW,
    LED_BLINK_FAST
} led_state_t;

typedef struct {
    float temperature;
    float humidity;
    garage_state_t state;
} garage_status_t;

// Global variables
static garage_state_t current_state = GARAGE_CLOSED;
static int current_angle = SERVO_CLOSED_ANGLE;
static esp_websocket_client_handle_t client;
static led_state_t current_led_state = LED_OFF;
static char wifi_ssid[32] = DEFAULT_WIFI_SSID;
static char wifi_pass[32] = DEFAULT_WIFI_PASS;
static char ws_uri[128] = DEFAULT_WS_URI;
static QueueHandle_t command_queue;
static TimerHandle_t status_timer;
static garage_status_t current_status = {0};
static SemaphoreHandle_t status_mutex;

// Function declarations
static void init_nvs(void);
static void init_wifi(void);
static void init_websocket(void);
static void led_task(void *pvParameters);
static void set_led_state(led_state_t state);
static void websocket_event_handler(void *handler_args, esp_event_base_t base, int32_t event_id, void *event_data);
static void wifi_event_handler(void* arg, esp_event_base_t event_base, int32_t event_id, void* event_data);

// NVS Functions
static void init_nvs(void) {
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    nvs_handle_t nvs_handle;
    ret = nvs_open("storage", NVS_READWRITE, &nvs_handle);
    if (ret == ESP_OK) {
        size_t required_size;
        ret = nvs_get_str(nvs_handle, "wifi_ssid", NULL, &required_size);
        if (ret == ESP_OK) {
            nvs_get_str(nvs_handle, "wifi_ssid", wifi_ssid, &required_size);
            nvs_get_str(nvs_handle, "wifi_pass", wifi_pass, &required_size);
            nvs_get_str(nvs_handle, "ws_uri", ws_uri, &required_size);
        }
        nvs_close(nvs_handle);
    }
}

// Servo Functions
static uint32_t servo_angle_to_duty(int angle) {
    uint32_t pulse_width = (angle * (SERVO_MAX_PULSEWIDTH_US - SERVO_MIN_PULSEWIDTH_US) / SERVO_MAX_DEGREE) + SERVO_MIN_PULSEWIDTH_US;
    return (1 << LEDC_DUTY_RES) * pulse_width / (1000000 / LEDC_FREQUENCY);
}

static void servo_init(void) {
    ledc_timer_config_t ledc_timer = {
        .speed_mode = LEDC_MODE,
        .duty_resolution = LEDC_DUTY_RES,
        .timer_num = LEDC_TIMER,
        .freq_hz = LEDC_FREQUENCY,
        .clk_cfg = LEDC_AUTO_CLK
    };
    ESP_ERROR_CHECK(ledc_timer_config(&ledc_timer));

    ledc_channel_config_t ledc_channel = {
        .speed_mode = LEDC_MODE,
        .channel = LEDC_CHANNEL,
        .timer_sel = LEDC_TIMER,
        .intr_type = LEDC_INTR_DISABLE,
        .gpio_num = LEDC_OUTPUT_IO,
        .duty = servo_angle_to_duty(SERVO_CLOSED_ANGLE),
        .hpoint = 0
    };
    ESP_ERROR_CHECK(ledc_channel_config(&ledc_channel));
}

void set_servo_angle(int angle) {
    uint32_t duty = servo_angle_to_duty(angle);
    ESP_ERROR_CHECK(ledc_set_duty(LEDC_MODE, LEDC_CHANNEL, duty));
    ESP_ERROR_CHECK(ledc_update_duty(LEDC_MODE, LEDC_CHANNEL));
}

static void status_timer_callback(TimerHandle_t xTimer) {
    int16_t temperature_i = 0;
    int16_t humidity_i = 0;
    
    if (dht_read_data(DHT_TYPE_AM2301, 3, &humidity_i, &temperature_i) == ESP_OK) {
        xSemaphoreTake(status_mutex, portMAX_DELAY);
        current_status.temperature = temperature_i / 10.0f;
        current_status.humidity = humidity_i / 10.0f;
        
        if (esp_websocket_client_is_connected(client)) {
            cJSON *root = cJSON_CreateObject();
            cJSON_AddStringToObject(root, "type", "status");
            cJSON_AddNumberToObject(root, "temperature", current_status.temperature);
            cJSON_AddNumberToObject(root, "humidity", current_status.humidity);
            cJSON_AddStringToObject(root, "state", 
                current_status.state == GARAGE_OPEN ? "open" : 
                current_status.state == GARAGE_CLOSED ? "closed" : "moving");
            
            char *json_string = cJSON_Print(root);
            esp_websocket_client_send_text(client, json_string, strlen(json_string), portMAX_DELAY);
            free(json_string);
            cJSON_Delete(root);
        }
        xSemaphoreGive(status_mutex);
    }
}

void move_servo_smooth(int target_angle) {
    current_state = GARAGE_MOVING;
    int step = (target_angle > current_angle) ? 1 : -1;
    
    while (current_angle != target_angle) {
        current_angle += step;
        set_servo_angle(current_angle);
        vTaskDelay(pdMS_TO_TICKS(SERVO_STEP_DELAY_MS));
    }
    
    current_state = (current_angle == SERVO_OPEN_ANGLE) ? GARAGE_OPEN : GARAGE_CLOSED;
    status_timer_callback(NULL);
}

static void servo_task(void *pvParameters) {
    int target_angle;
    
    while (1) {
        if (xQueueReceive(command_queue, &target_angle, portMAX_DELAY) == pdTRUE) {
            xSemaphoreTake(status_mutex, portMAX_DELAY);
            current_status.state = GARAGE_MOVING;
            xSemaphoreGive(status_mutex);

            int step = (target_angle > current_angle) ? 1 : -1;
            
            while (current_angle != target_angle) {
                current_angle += step;
                set_servo_angle(current_angle);
                vTaskDelay(pdMS_TO_TICKS(SERVO_STEP_DELAY_MS));
            }
            
            xSemaphoreTake(status_mutex, portMAX_DELAY);
            current_status.state = (current_angle == SERVO_OPEN_ANGLE) ? GARAGE_OPEN : GARAGE_CLOSED;
            xSemaphoreGive(status_mutex);
        }
    }
}

// Network Functions
static void init_wifi(void) {
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, &wifi_event_handler, NULL));
    ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, &wifi_event_handler, NULL));

    wifi_config_t wifi_config = {
        .sta = {
            .threshold.authmode = WIFI_AUTH_WPA2_PSK,
        },
    };
    memcpy(wifi_config.sta.ssid, wifi_ssid, sizeof(wifi_config.sta.ssid));
    memcpy(wifi_config.sta.password, wifi_pass, sizeof(wifi_config.sta.password));

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());
}

static void init_websocket(void) {
    esp_websocket_client_config_t websocket_cfg = {
        .uri = ws_uri,
        .reconnect_timeout_ms = 2000,
    };
    client = esp_websocket_client_init(&websocket_cfg);
    esp_websocket_register_events(client, WEBSOCKET_EVENT_ANY, websocket_event_handler, NULL);
}

// Status LED Functions
static void set_led_state(led_state_t state) {
    current_led_state = state;
}

static void led_task(void *pvParameters) {
    gpio_set_direction(LED_PIN, GPIO_MODE_OUTPUT);
    
    while(1) {
        switch(current_led_state) {
            case LED_OFF:
                gpio_set_level(LED_PIN, 0);
                vTaskDelay(pdMS_TO_TICKS(1000));
                break;
            case LED_ON:
                gpio_set_level(LED_PIN, 1);
                vTaskDelay(pdMS_TO_TICKS(1000));
                break;
            case LED_BLINK_SLOW:
                gpio_set_level(LED_PIN, 1);
                vTaskDelay(pdMS_TO_TICKS(1000));
                gpio_set_level(LED_PIN, 0);
                vTaskDelay(pdMS_TO_TICKS(1000));
                break;
            case LED_BLINK_FAST:
                gpio_set_level(LED_PIN, 1);
                vTaskDelay(pdMS_TO_TICKS(200));
                gpio_set_level(LED_PIN, 0);
                vTaskDelay(pdMS_TO_TICKS(200));
                break;
        }
    }
}

void app_main(void) {
    // Initialize components
    init_nvs();
    servo_init();
    set_servo_angle(SERVO_CLOSED_ANGLE);
    
    // Create synchronization primitives
    command_queue = xQueueCreate(5, sizeof(int));
    status_mutex = xSemaphoreCreateMutex(); // Corrected mutex creation
    
    // Create status timer
    status_timer = xTimerCreate(
        "StatusTimer",
        pdMS_TO_TICKS(UPDATE_INTERVAL_MS),
        pdTRUE,
        0,
        status_timer_callback
    );
    
    // Initialize current status
    current_status.state = GARAGE_CLOSED;
    
    // Create tasks
    xTaskCreate(led_task, "led_task", 2048, NULL, 5, NULL);
    xTaskCreate(servo_task, "servo_task", 4096, NULL, 5, NULL);
    
    // Initialize network
    init_wifi();
    init_websocket();
    
    // Main task can now be used for system monitoring or other purposes
    while(1) {
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

// Event Handlers
static void websocket_event_handler(void *handler_args, esp_event_base_t base, int32_t event_id, void *event_data) {
    esp_websocket_event_data_t *data = (esp_websocket_event_data_t *)event_data;
    
    switch (event_id) {
        case WEBSOCKET_EVENT_CONNECTED:
            ESP_LOGI("WS", "CONNECTED");
            set_led_state(LED_ON);
            // Start the status timer when connected
            xTimerStart(status_timer, 0);
            break;
            
        case WEBSOCKET_EVENT_DISCONNECTED:
            ESP_LOGI("WS", "DISCONNECTED");
            set_led_state(LED_BLINK_SLOW);
            // Stop the status timer when disconnected
            xTimerStop(status_timer, 0);
            break;
            
        case WEBSOCKET_EVENT_DATA:
            if(data->op_code == 1) {
                char json_str[256];
                memcpy(json_str, data->data_ptr, data->data_len);
                json_str[data->data_len] = 0;
                
                cJSON *root = cJSON_Parse(json_str);
                if (root) {
                    cJSON *command = cJSON_GetObjectItem(root, "command");
                    if (command && command->type == cJSON_String) {
                        int target_angle = -1;
                        
                        if (strcmp(command->valuestring, "open") == 0) {
                            target_angle = SERVO_OPEN_ANGLE;
                        } else if (strcmp(command->valuestring, "close") == 0) {
                            target_angle = SERVO_CLOSED_ANGLE;
                        }
                        
                        if (target_angle != -1) {
                            xQueueSend(command_queue, &target_angle, 0);
                        }
                    }
                    cJSON_Delete(root);
                }
            }
            break;
    }
}

static void wifi_event_handler(void* arg, esp_event_base_t event_base, int32_t event_id, void* event_data) {
    if (event_base == WIFI_EVENT) {
        switch(event_id) {
            case WIFI_EVENT_STA_START:
                esp_wifi_connect();
                set_led_state(LED_BLINK_FAST);
                break;
            case WIFI_EVENT_STA_DISCONNECTED:
                esp_wifi_connect();
                set_led_state(LED_BLINK_FAST);
                break;
        }
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        set_led_state(LED_BLINK_SLOW);
        esp_websocket_client_start(client);
    }
}