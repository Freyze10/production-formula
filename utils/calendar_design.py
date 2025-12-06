STYLESHEET = """
QCalendarWidget {
    background-color: #ffffff; 
    border: 1px solid #e2e8f0; 
    border-radius: 10px; 
    font-family: 'Segoe UI', 'Arial', sans-serif; 
    font-size: 12px; 
    color: #2d3748; 
    min-height: 230px; 
    min-width: 370px; 
}

/* Header (Month and Year navigation) */
QCalendarWidget QWidget#qt_calendar_navigationbar {
    background-color: #f7fafc; 
    border-top-left-radius: 9px;
    border-top-right-radius: 9px;
    height: 48px; 
    padding: 5px;
}

/* --- FIXED SECTION START --- */

/* Navigation buttons (Previous/Next specific IDs) */
QCalendarWidget #qt_calendar_prevmonth, 
QCalendarWidget #qt_calendar_nextmonth {
    background-color: transparent;
    border: none;
    color: #2d3748; 
    font-size: 14px;
    padding: 8px;
    margin: 4px;
    min-width: 32px; 
    qproperty-icon: none; /* Optional: hides default arrow icons if using text */
}

QCalendarWidget #qt_calendar_prevmonth:hover, 
QCalendarWidget #qt_calendar_nextmonth:hover {
    background-color: #edf2f7; 
    border-radius: 6px;
}

QCalendarWidget #qt_calendar_prevmonth:pressed, 
QCalendarWidget #qt_calendar_nextmonth:pressed {
    background-color: #cbd5e0; 
}

/* Year Editor (QSpinBox) styling */
QCalendarWidget QSpinBox {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    color: #2d3748;
    font-size: 14px;
    padding-left: 5px;
    selection-background-color: #3182ce;
    selection-color: white;
    min-width: 70px; /* Ensure enough width for the year text */
    margin-right: 5px;
}

/* Style the internal Up/Down arrows of the year editor */
QCalendarWidget QSpinBox::up-button, 
QCalendarWidget QSpinBox::down-button {
    subcontrol-origin: border;
    width: 20px; /* Keep these small */
    border: none;
    background: transparent;
}

QCalendarWidget QSpinBox::up-button:hover, 
QCalendarWidget QSpinBox::down-button:hover {
    background-color: #edf2f7;
}

/* --- FIXED SECTION END --- */

/* Month and Year Label */
QCalendarWidget QWidget#qt_calendar_navigationbar QLabel {
    color: #1a202c; 
    font-size: 14px; 
    font-weight: 600; 
}

/* Days of the week (Mon, Tue, Wed...) */
QCalendarWidget QAbstractItemView:enabled {
    outline: none; 
    background-color: #ffffff; 
    font-size: 12px; 
    color: #2d3748; 
    min-height: 25px; 
    min-width: 280px; 
}

/* Day grid selection and hover */
QCalendarWidget QAbstractItemView {
    selection-background-color: #3182ce; 
    selection-color: #ffffff; 
    padding: 5px; 
    min-height: 200px; 
    min-width: 280px; 
}

/* Day cells */
QCalendarWidget QAbstractItemView::item {
    border: 1px solid transparent; 
    padding: 6px; 
    margin: 2px; 
    border-radius: 8px; 
    min-height: 25px; 
    font-size: 12px; 
    color: #2d3748; 
    min-width: 30px; 
}

/* Highlight current/selected date */
QCalendarWidget QAbstractItemView::item:selected {
    background-color: #3182ce; 
    color: #ffffff; 
    border-radius: 8px; 
    font-weight: 600; 
}

/* Hover effect for non-selected days */
QCalendarWidget QAbstractItemView::item:!selected:hover {
    background-color: #e6f0fa; 
    border-radius: 8px;
}

/* Today button */
#qt_calendar_today_button {
    background-color: #4c51bf; 
    color: #ffffff; 
    border: none;
    border-radius: 6px;
    padding: 8px 12px; 
    margin: 6px;
    font-size: 12px;
    font-weight: 500;
}
#qt_calendar_today_button:hover {
    background-color: #434190; 
}

/* Clear button */
#qt_calendar_clear_button {
    background-color: #f56565; 
    color: #ffffff; 
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    margin: 6px;
    font-size: 12px;
    font-weight: 500;
}
#qt_calendar_clear_button:hover {
    background-color: #c53030; 
}

/* Weekend days */
QCalendarWidget QAbstractItemView::item:!selected[date_in_weekend="true"] {
    color: #e53e3e; 
}

/* Days not in the current month */
QCalendarWidget QAbstractItemView::item:!selected[date_in_current_month="false"] {
    color: #a0aec0; 
}

/* Ensure table corner matches background */
QCalendarWidget QTableView QTableCornerButton::section {
    background-color: #ffffff; 
    border: none;
}
"""