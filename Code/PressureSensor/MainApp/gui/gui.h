/*
 * gui.h
 *
 *  Created on: May 13, 2019
 *      Author: kakareka
 */
#ifndef GUI_H_
#define GUI_H_

typedef enum {
    UR,
    UL,
    LL,
    LR,
    ML
} BUTTON_LOC_T;

void gui_init(void);
void gui_switch_to_main(void);
void gui_switch_to_config(void);
void gui_display(void);
void gui_toggle_button(BUTTON_LOC loc);
void gui_update_mpsi(int mpsi);

#endif /* GUI_H_ */
