STYLESHEET = """
QCalendarWidget {
    background-color: #ffffff; /* Clean white background */
    border: 1px solid #e2e8f0; /* Subtle gray border */
    border-radius: 10px; /* Softer rounded corners */
    font-family: 'Segoe UI', 'Arial', sans-serif; /* Modern, readable font */
    font-size: 12px; /* Comfortable font size */
    color: #2d3748; /* Dark gray for text readability */
    min-height: 230px; /* Ensure enough height for full month */
    min-width: 370px; /* Ensure enough width for day names */
}

/* Header (Month and Year navigation) */
QCalendarWidget QWidget#qt_calendar_navigationbar {
    background-color: #f7fafc; /* Light gray header background */
    border-top-left-radius: 9px;
    border-top-right-radius: 9px;
    height: 48px; /* Slightly taller for better touch/click area */
    min-width: 150px;
    padding: 5px;
}

/* Navigation buttons (Previous/Next) */
QCalendarWidget QAbstractButton {
    background-color: transparent;
    border: none;
    color: #2d3748; /* Dark gray for contrast */
    font-size: 14px; /* Larger for better visibility */
    padding: 8px;
    margin: 4px;
    min-width: 32px; /* Ensure buttons are clickable */
}

QCalendarWidget QAbstractButton:hover {
    background-color: #edf2f7; /* Subtle hover effect */
    border-radius: 6px;
}

QCalendarWidget QAbstractButton:pressed {
    background-color: #cbd5e0; /* Slightly darker when pressed */
}

/* Month and Year Label */
QCalendarWidget QWidget#qt_calendar_navigationbar QLabel {
    color: #1a202c; /* Darker for emphasis */
    font-size: 14px; /* Larger for clarity */
    font-weight: 600; /* Semi-bold for prominence */
}

/* Days of the week (Mon, Tue, Wed...) */
QCalendarWidget QAbstractItemView:enabled {
    outline: none; /* Remove focus outline for cleaner look */
    background-color: #ffffff; /* White background for grid */
    font-size: 12px; /* Ensure day names are readable */
    color: #2d3748; /* Dark gray for contrast */
    min-height: 25px; /* Increased height for day headers */
    min-width: 280px; /* Ensure enough width for day names */
}

/* Day grid selection and hover */
QCalendarWidget QAbstractItemView {
    selection-background-color: #3182ce; /* Pleasant blue for selected date */
    selection-color: #ffffff; /* White text for contrast */
    padding: 5px; /* Reduced padding to fit more days */
    min-height: 200px; /* Ensure enough height for full grid */
    min-width: 280px; /* Ensure enough width for full grid */
}

/* Day cells */
QCalendarWidget QAbstractItemView::item {
    border: 1px solid transparent; /* No default border */
    padding: 6px; /* Slightly reduced padding for more rows */
    margin: 2px; /* Reduced margin for tighter layout */
    border-radius: 8px; /* Rounded corners for day cells */
    min-height: 25px; /* Adjusted for better fit */
    font-size: 12px; /* Consistent readable font size */
    color: #2d3748; /* Dark gray for all day text */
    min-width: 30px; /* Minimum width for day cells */
}

/* Highlight current/selected date */
QCalendarWidget QAbstractItemView::item:selected {
    background-color: #3182ce; /* Blue for selected date */
    color: #ffffff; /* White text for contrast */
    border-radius: 8px; /* Consistent rounding */
    font-weight: 600; /* Semi-bold for emphasis */
}

/* Hover effect for non-selected days */
QCalendarWidget QAbstractItemView::item:!selected:hover {
    background-color: #e6f0fa; /* Light blue hover effect */
    border-radius: 8px;
}

/* Today button */
#qt_calendar_today_button {
    background-color: #4c51bf; /* Vibrant indigo for today button */
    color: #ffffff; /* White text */
    border: none;
    border-radius: 6px;
    padding: 8px 12px; /* Comfortable padding */
    margin: 6px;
    font-size: 12px;
    font-weight: 500;
}

#qt_calendar_today_button:hover {
    background-color: #434190; /* Slightly darker on hover */
}

/* Clear button */
#qt_calendar_clear_button {
    background-color: #f56565; /* Soft red for clear button */
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    margin: 6px;
    font-size: 12px;
    font-weight: 500;
}

#qt_calendar_clear_button:hover {
    background-color: #c53030; /* Darker red on hover */
}

/* Weekend days */
QCalendarWidget QAbstractItemView::item:!selected[date_in_weekend="true"] {
    color: #e53e3e; /* Red for weekends, consistent with original */
}

/* Days not in the current month */
QCalendarWidget QAbstractItemView::item:!selected[date_in_current_month="false"] {
    color: #a0aec0; /* Muted gray for non-current month days */
}

/* Ensure table corner matches background */
QCalendarWidget QTableView QTableCornerButton::section {
    background-color: #ffffff; /* Match main background */
    border: none;
}
"""