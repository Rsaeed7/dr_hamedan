pip install smsir-python

How to use

Create an instance:

from sms_ir import SmsIr
sms_ir = SmsIr(
api_key,
linenumber,
)
Send message to a specific mobile number:

sms_ir.send_sms(
number,
message,
linenumber,
)
Send message to multiple mobile numbers:

sms_ir.send_bulk_sms(
numbers,
message,
linenumber,
)
Send multiple messages to multiple mobile numbers one-to-one:

sms_ir.send_like_to_like(
numbers,
messages,
linenumber,
send_date_time,
)
Delete scheduled message:

sms_ir.delete_scheduled(
pack_id,
)
Send verification code with predefined template:

sms_ir.send_verify_code(
number,
template_id,
parameters,
)
Get report of sent message:

sms_ir.report_message(
message_id,
)
Get report of sent message pack:

sms_ir.report_pack(
pack_id,
))
Get report of messages sent today:

sms_ir.report_today(
page_size,
page_number,
))
Get report from archived messages:

sms_ir.report_archived(
from_date,
to_date,
page_size,
page_number,
))
Get report of latest received messages:

sms_ir.report_latest_received(
count,
)
Get report of messages received today:

sms_ir.report_today_received(
page_size,
page_number,
)
Get report of messages received today:

sms_ir.report_archived_received(
from_date,
to_date,
page_size,
page_number,
)
Get account credit:

sms_ir.get_credit()
Get account line numbers:

sms_ir.get_line_numbers()