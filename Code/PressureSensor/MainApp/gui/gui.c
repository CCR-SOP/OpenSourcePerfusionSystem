#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gui.h"
#include "grlib.h"
#include "button.h"

extern Graphics_Context g_sContext;
extern uint16_t g_high_mpsi;
extern uint16_t g_low_mpsi;
extern uint16_t g_mpsi;

typedef enum {
    MAIN,
    CONFIG
} PANEL_MODE_T;

typedef Graphics_Button Button;
typedef int8_t Text_t;

bool is_button(Button* btn, int x, int y);

static const uint32_t g_color_btnfill_normal = GRAPHICS_COLOR_RED;
static const uint32_t g_color_btnfill_selected = GRAPHICS_COLOR_GREEN;
static const uint32_t g_color_btntext_normal = GRAPHICS_COLOR_GREEN;
static const uint32_t g_color_btntext_selected = GRAPHICS_COLOR_RED;
#define BTN_FONT g_sFontCm18
static const uint32_t g_color_btnborder = GRAPHICS_COLOR_WHITE;
static const uint8_t g_border_width = 1;
static const uint8_t g_btn_height = 60;
static const uint8_t g_btn_width = 100;

static const int g_display_border = 5;

static Button btn_title;
static Button btn_subtitle;
#define TITLE_FONT g_sFontCm18
#define SUBTITLE_FONT g_sFontCm18

static Text_t lbl_title[] = "NIH Bladder Control v1.0";
// Main Panel
static Button btn_cyclectrl;
Text_t lbl_cyclectrl[] = "Cycle";
static Button btn_mpsi;
Text_t lbl_mpsi[] = "0000";
static Button btn_inflate;
Text_t lbl_inflate[] = "Inflate";
static Button btn_deflate;
Text_t lbl_deflate[] = "Deflate";
static Button btn_config;
Text_t lbl_config[] = "Config";
static Text_t panel_title_main[] = "Control";


// Config Panel
static Button btn_plus;
Text_t lbl_plus[] = "+";
static Button btn_minus;
Text_t lbl_minus[] = "-";
static Button btn_highlow;
Text_t lbl_high[] = "High";
Text_t lbl_low[] = "Low";
static Button btn_main;
Text_t lbl_main[] = "Control";
static Text_t panel_title_config[] = "Configuration";

typedef struct {
    Button *btn_ur;
    Button *btn_lr;
    Button *btn_ul;
    Button *btn_ml;
    Button *btn_ll;
    PANEL_MODE_T mode;
} PANEL_T;

static PANEL_T g_panel;

static void toggle_button(Button* btn);

static void create_button(Button* btn, int x, int y,
                          int w, int h,
                          int8_t* lbl)
{
    btn->xMin = x;
    btn->xMax = x + w;
    btn->yMin = y;
    btn->yMax = y + h;

    btn->borderWidth = g_border_width;
    btn->borderColor = g_color_btnborder;
    btn->fillColor = g_color_btnfill_normal;
    btn->selectedColor = g_color_btnfill_selected;
    btn->textColor = g_color_btntext_normal;
    btn->selectedTextColor = g_color_btntext_selected;

    btn->selected = false;
    btn->text = lbl;

    btn->font = &BTN_FONT;

    // text_len will not be accurate for fonts with different
    // width characters
    int text_width = Graphics_getStringWidth(&g_sContext, lbl, strlen((const char*)lbl));
    btn->textXPos = (w - text_width) / 2 + btn->xMin;
    btn->textYPos = (h - BTN_FONT.height) / 2 + btn->yMin;
}

static void init_buttons(void)
{
    int display_w = Graphics_getDisplayWidth(&g_sContext);
    int display_h = Graphics_getDisplayHeight(&g_sContext);


    // title button is not really a button, but convenient to use
    create_button(&btn_title, g_display_border, g_display_border,
                  display_w - 2 * g_display_border, TITLE_FONT.height, lbl_title);
    btn_title.fillColor = GRAPHICS_COLOR_BLACK;
    btn_title.textColor = GRAPHICS_COLOR_WHITE;
    btn_title.borderWidth = 0;
    create_button(&btn_subtitle, btn_title.xMin, btn_title.yMax + 1,
                  btn_title.xMax - btn_title.xMin, SUBTITLE_FONT.height, "Control");
    btn_subtitle.fillColor = GRAPHICS_COLOR_BLACK;
    btn_subtitle.textColor = GRAPHICS_COLOR_WHITE;
    btn_subtitle.borderWidth = 0;

    // control buttons
    int col1_x = g_display_border;
    int col2_x = display_w - g_display_border - g_btn_width;
    int row_top_y = btn_subtitle.yMax + 5;
    int row_bot_y = display_h - g_display_border - g_btn_height;
    int spacing = (row_bot_y - (row_top_y + g_btn_height) - g_btn_height) / 2;
    int row_mid_y = row_top_y + g_btn_height + spacing;

    // Main panel
    create_button(&btn_cyclectrl, col1_x, row_top_y,
                  g_btn_width, g_btn_height, lbl_cyclectrl);
    create_button(&btn_mpsi, col1_x, row_mid_y,
                  g_btn_width, g_btn_height, lbl_mpsi);
    create_button(&btn_inflate, col1_x, row_bot_y,
                  g_btn_width, g_btn_height, lbl_inflate);

    create_button(&btn_config, col2_x, row_top_y,
                  g_btn_width, g_btn_height, lbl_config);
    create_button(&btn_deflate, col2_x, row_bot_y,
                  g_btn_width, g_btn_height, lbl_deflate);

    // Config panel
    create_button(&btn_plus, col1_x, row_top_y,
                  g_btn_width, g_btn_height, lbl_plus);
    create_button(&btn_mpsi, col1_x, row_mid_y,
                  g_btn_width, g_btn_height, lbl_mpsi);
    create_button(&btn_minus, col1_x, row_bot_y,
                  g_btn_width, g_btn_height, lbl_minus);

    create_button(&btn_main, col2_x, row_top_y,
                  g_btn_width, g_btn_height, lbl_main);
    create_button(&btn_highlow, col2_x, row_bot_y,
                  g_btn_width, g_btn_height, lbl_high);

}

void gui_init(void)
{
    init_buttons();
    gui_switch_to_main();
}

inline bool gui_is_mode_config(void)
{
    return (g_panel.mode == CONFIG);
}

inline bool gui_is_mode_main(void)
{
    return (g_panel.mode == MAIN);
}

inline bool gui_is_highmode(void)
{
    return (!btn_highlow.selected);
}

inline bool gui_is_lowmode(void)
{
    return (btn_highlow.selected);
}

void gui_switch_to_main(void)
{
    g_panel.mode = MAIN;
    btn_subtitle.text = panel_title_main;
    g_panel.btn_ul = &btn_cyclectrl;
    g_panel.btn_ml = &btn_mpsi;
    g_panel.btn_lr = &btn_deflate;

    g_panel.btn_ur = &btn_config;
    g_panel.btn_ll = &btn_inflate;

    gui_display();
}

void gui_switch_to_config(void)
{
    g_panel.mode = CONFIG;
    btn_subtitle.text = panel_title_config;
    g_panel.btn_ul = &btn_plus;
    g_panel.btn_ml = &btn_mpsi;
    g_panel.btn_ll = &btn_minus;

    g_panel.btn_ur = &btn_main;
    g_panel.btn_lr = &btn_highlow;

    gui_display();

}

void gui_display(void)
{

    gui_update_mpsi();
    Graphics_drawButton(&g_sContext, &btn_title);
    Graphics_drawButton(&g_sContext, &btn_subtitle);

    Graphics_drawButton(&g_sContext, g_panel.btn_ul);
    Graphics_drawButton(&g_sContext, g_panel.btn_ml);
    Graphics_drawButton(&g_sContext, g_panel.btn_ll);

    Graphics_drawButton(&g_sContext, g_panel.btn_ur);
    Graphics_drawButton(&g_sContext, g_panel.btn_lr);



}

void gui_toggle_inflate(void)
{
    toggle_button(&btn_inflate);
}

void gui_toggle_deflate(void)
{
    toggle_button(&btn_deflate);
}

void gui_toggle_cycle(void)
{
    toggle_button(&btn_cyclectrl);
}

void gui_toggle_highlow(void)
{
    // Swap text
    // remember: selected var has not been toggled yet
    if (btn_highlow.selected) {
        btn_highlow.text = lbl_high;
    } else {
        btn_highlow.text = lbl_low;
    }
    toggle_button(&btn_highlow);
    gui_update_mpsi();
}

void toggle_button(Button* btn)
{
    btn->selected = !(btn->selected);
    Graphics_drawButton(&g_sContext, btn);
}

void gui_update_mpsi(void)
{
    int16_t mpsi = 0;
    if (g_panel.mode == MAIN) {
        mpsi = g_mpsi;
    } else {
        if (btn_highlow.selected) {
            mpsi = g_low_mpsi;
        } else {
            mpsi = g_high_mpsi;
        }
    }
    sprintf((char*)lbl_mpsi, "%04d", mpsi);
    Graphics_drawButton(&g_sContext, &btn_mpsi);

}

bool is_button(Button* btn, int x, int y)
{
    return Graphics_isButtonSelected(btn, x, y);
}

bool gui_is_cycle(int x, int y) {
    return (g_panel.mode == MAIN && is_button(&btn_cyclectrl, x, y));
}

bool gui_is_inflate(int x, int y) {
    return (g_panel.mode == MAIN && is_button(&btn_inflate, x, y));
}

bool gui_is_deflate(int x, int y) {
    return (g_panel.mode == MAIN && is_button(&btn_deflate, x, y));
}


bool gui_is_config(int x, int y) {
    return (g_panel.mode == MAIN && is_button(&btn_config, x, y));
}

bool gui_is_plus(int x, int y) {
    return (g_panel.mode == CONFIG && is_button(&btn_plus, x, y));
}

bool gui_is_minus(int x, int y) {
    return (g_panel.mode == CONFIG && is_button(&btn_minus, x, y));
}

bool gui_is_highlow(int x, int y) {
    return (g_panel.mode == CONFIG && is_button(&btn_highlow, x, y));
}

bool gui_is_main(int x, int y) {
    return (g_panel.mode == CONFIG && is_button(&btn_main, x, y));
}

