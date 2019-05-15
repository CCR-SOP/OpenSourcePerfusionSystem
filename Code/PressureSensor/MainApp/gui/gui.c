#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gui.h"
#include "grlib.h"
#include "button.h"


typedef enum {
    MAIN,
    CONFIG
} PANEL_MODE_T;

typedef int8_t Text_t;
typedef Graphics_Button Button;

bool is_button(Button* btn, int x, int y);

extern Graphics_Context g_sContext;

static const uint32_t g_color_btnfill_normal = GRAPHICS_COLOR_RED;
static const uint32_t g_color_btnfill_selected = GRAPHICS_COLOR_GREEN;
static const uint32_t g_color_btntext_normal = GRAPHICS_COLOR_GREEN;
static const uint32_t g_color_btntext_selected = GRAPHICS_COLOR_RED;
#define BTN_FONT g_sFontCm18
static const uint32_t g_color_btnborder = GRAPHICS_COLOR_WHITE;
static const uint8_t g_border_width = 1;
static const uint8_t g_btn_height = 10;
static const uint8_t g_btn_width = 40;

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
Text_t lbl_main[] = "Main";
static Text_t panel_title_config[] = "Configuration";

typedef struct {
    Button *btn_title;
    Button *btn_subtitle;
    Button *btn_ur;
    Button *btn_lr;
    Button *btn_ul;
    Button *btn_ml;
    Button *btn_ll;
    PANEL_MODE_T mode;
} PANEL_T;

static PANEL_T g_panel;


static void create_button(Graphics_Button* btn, int x, int y,
                          int w, int h,
                          int8_t* lbl)
{
    btn->xMin = x;
    btn->xMax = x + w;
    btn->yMin = y;
    btn->yMax = y + h;

    btn->selected = false;
    btn->borderWidth = g_border_width;
    btn->borderColor = g_color_btnborder;
    btn->fillColor = g_color_btnfill_normal;
    btn->selectedColor = g_color_btnfill_selected;
    btn->textColor = g_color_btntext_normal;
    btn->selectedTextColor = g_color_btntext_selected;

    btn->text = lbl;
    btn->font = &BTN_FONT;

    // text_len will not be accurate for fonts with different
    // width characters
    int text_width = Graphics_getStringWidth(&g_sContext, lbl, strlen((const char*)lbl));
    btn->textXPos = (w - text_width) / 2;
    btn->textYPos = (h - BTN_FONT.height) / 2;
}

static void init_buttons(void)
{
    int display_w = Graphics_getDisplayWidth(&g_sContext);
    int display_h = Graphics_getDisplayHeight(&g_sContext);


    // title button is not really a button, but convenient to use
    create_button(&btn_title, 0, 0,
                  display_w, TITLE_FONT.height, lbl_title);
    create_button(&btn_subtitle, 0, btn_title.yMax + 1,
                  display_w, SUBTITLE_FONT.height, "");

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

void gui_switch_to_main(void)
{
    g_panel.mode = MAIN;
    btn_subtitle.text = panel_title_main;
    g_panel.btn_ul = &btn_cyclectrl;
    g_panel.btn_ml = &btn_mpsi;
    g_panel.btn_lr = &btn_deflate;

    g_panel.btn_ur = &btn_config;
    g_panel.btn_ll = &btn_inflate;

}

void gui_switch_to_config(void)
{
    g_panel.mode = CONFIG;
    btn_subtitle.text = panel_title_config;
    g_panel.btn_ul = &btn_plus;
    g_panel.btn_ml = &btn_mpsi;
    g_panel.btn_ll = &btn_minus;

    g_panel.btn_ur = &btn_main;
    g_panel.btn_ll = &btn_highlow;

}

void gui_display(void)
{
    Graphics_drawButton(&g_sContext, g_panel.btn_title);
    Graphics_drawButton(&g_sContext, g_panel.btn_subtitle);

    Graphics_drawButton(&g_sContext, g_panel.btn_ul);
    Graphics_drawButton(&g_sContext, g_panel.btn_ml);
    Graphics_drawButton(&g_sContext, g_panel.btn_ll);

    Graphics_drawButton(&g_sContext, g_panel.btn_ur);
    Graphics_drawButton(&g_sContext, g_panel.btn_lr);


}

void gui_toggle_inflate(void)
{
    gui_toggle_button(LL);
}

void gui_toggle_deflate(void)
{
    gui_toggle_button(LR);
}

void gui_toggle_cycle(void)
{
    gui_toggle_button(UL);
}

void gui_toggle_button(BUTTON_LOC_T loc)
{
    Button* btn;
    switch(loc) {
    case UR:
        btn = g_panel.btn_ur;
        break;
    case UL:
        btn= g_panel.btn_ul;
        break;
    case LR:
        btn = g_panel.btn_lr;
        break;
    case LL:
        btn= g_panel.btn_ll;
        break;
    case ML:
        btn= g_panel.btn_ml;
        break;
    default:
        assert("ILLEGAL BUTTON TOGGLE");
    }
    Graphics_drawButton(&g_sContext, btn);
}

void gui_update_mpsi(int mpsi)
{
    if (g_panel.mode == MAIN) {
        sprintf((char*)lbl_mpsi, "%04d", mpsi);
        Graphics_drawButton(&g_sContext, &btn_mpsi);
    }
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
    return (g_panel.mode == MAIN && is_button(&btn_main, x, y));
}

