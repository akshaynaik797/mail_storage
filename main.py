from settings import hospital_data, pdfconfig, file_no, file_blacklist, conn_data
from mail_storage import gmail_api, graph_api, imap_

for hosp, data in hospital_data.items():
    if data['mode'] == 'gmail_api':
        # print(hosp)
        # gmail_api(data, hosp)
        pass
    elif data['mode'] == 'graph_api':
        # print(hosp)
        # graph_api(data, hosp)
        pass
    elif data['mode'] == 'imap_':
        imap_(data, hosp)
    pass