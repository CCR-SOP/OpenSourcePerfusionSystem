/*
 * gui.h
 *
 *  Created on: May 13, 2019
 *      Author: kakareka
 */
#ifndef GUI_H_
#define GUI_H_

#include <stdbool.h>


void gui_init(void);
void gui_switch_to_main(void);
void gui_switch_to_config(void);
void gui_display(void);
void gui_toggle_inflate(void);
void gui_toggle_deflate(void);
void gui_toggle_cycle(void);
void gui_toggle_highlow(void);
void gui_update_mpsi(void);


bool gui_is_inflate(int x, int y);
bool gui_is_deflate(int x, int y);
bool gui_is_cycle(int x, int y);
bool gui_is_config(int x, int y);

bool gui_is_plus(int x, int y);
bool gui_is_minus(int x, int y);
bool gui_is_highlow(int x, int y);
bool gui_is_main(int x, int y);

inline bool gui_is_mode_config(void);
inline bool gui_is_mode_main(void);
inline bool gui_is_highmode(void);
inline bool gui_is_lowmode(void);


#endif /* GUI_H_ */
