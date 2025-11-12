
def send_email_with_excel (df_dict, recipient_email, excel_fn, subject):

    """
    Create a multi-tab Excel from a dictionary of DataFrames and send it via email.

    Parameters:
        df_dict (dict): {
                        'SheetName_1': DataFrame_1,
                        'Sheetname_2' : DataFrame_2    ...}

        recipient_email (str or list of string): One or more recipient email addresses
        excel_fn (str): Excel filename to be used in the  attachment , with  the excel extension ".xlsx"
        subject (str): Email subject

    # df_dict is a dictionary where
    #           1) key is tab/sheet name
    #           2) value is the dataframe to convert to excel
    """

    from email.message import EmailMessage
    from io import BytesIO
    import smtplib
    import ssl
    import os
    from dotenv import load_dotenv

    # load the environment variables from the .env file
    # ensure to gitignore this if git is used
    # load_dotenv()
    # sender_email = os.getenv('from_email')
    # sender_email_pwd = os.getenv('from_email_password')
    # sender_smtp_name = os.getenv('smtp_name')
    # sender_email_port = os.getenv('port_number_for_SMTP_SSL')
    # load_dotenv()
    sender_email = 'ppsycho109@gmail.com'
    sender_email_pwd = 'brantbrant!!!'
    sender_smtp_name = 'mail.polycolor.biz'
    sender_email_port = 465



    # Ensure recipient_email is a list
    if isinstance(recipient_email, str):
        recipient_email = [recipient_email]

    # Convert dictionary of DataFrames to multi-tab Excel in memory
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        for sheet_name, df in df_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    excel_buffer.seek(0)

    # Build the email
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = ', '.join(recipient_email)
    msg.set_content('Please find the attached Excel report.')

    # Attach the Excel file
    msg.add_attachment(
        excel_buffer.read(),
        maintype='application',
        subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        filename=excel_fn
    )

    # Send the email
    context = ssl.create_default_context()
    with smtplib.SMTP(sender_smtp_name,  sender_email_port) as server:
        server.starttls(context=context)
        server.login(sender_email, sender_email_pwd)
        server.send_message(msg, from_addr=sender_email, to_addrs=recipient_email)

    # line below optional
    print(f"\n\nEmail with file attachment name :  <{excel_fn}> sent to {recipient_email}")



# test script below
import pandas as pd
df_dict = {
    'Tab_1': pd.DataFrame({'A': [1, 2], 'B': [3, 4]}),
    'Tab_2': pd.DataFrame({'C': [5, 6], 'D': [7, 8]})
}

# Any of the 2 lines below will work
#   if one email, a string
#   if many email, multiple strings in a LIST (ie send to multiple emails)
recipient_email = 'bjabillanoza@gmail.com'
# recipient_email = ['esapci@gmail.com','esapci@yahoo.com']


excel_fn = 'test_excel.xlsx'
subject = 'Test Subject'
send_email_with_excel(df_dict, recipient_email, excel_fn, subject)


