from core.gmail.tools import LibSenseEmail

service = LibSenseEmail()
service.send_message("yw3752@nyu.edu", "Barry", "Rush-Local", 53, ["temp/Report-Rush-Local-2022-04-27.csv"])