<!-- - ارسال نظیر به نظیر -->
این متد برای ارسال به گروهی از موبایل‌ها با متن‌های متفاوت برای هر کدام، مورد استفاده قرار می‌گیرد. همچنین شما می‌توانید با مقداردهی به پارامتر زمان ارسال، از قابلیت ارسال پیامک زمانبندی شده نیز استفاده نمایید.

URL

https://api.sms.ir/v1/send/likeToLike
Request Method
POST
حداکثر تعداد مجاز شماره‌های مقصد 100 می‌باشد.

برای ارسال زمانبندی شده، انتخاب زمان گذشته نامعتبر می‌باشد.

برای ارسال زمانبندی شده، زمان معتبر می‎‌تواند در بازه یک ساعت آینده تا حداکثر 365 روز آینده در نظر گرفته شود.

تعداد شماره موبایل‌ها و متن‌های پیامک باید برابر باشند.

پارامترهای بدنه درخواست

مشخصه	ارسال	نوع	توضیح
lineNumber	اجباری	Long	شماره خط ارسالی
MessageTexts	اجباری	Array of String	متن های پیام کوتاه
Mobiles	اجباری	Array of String	شماره موبایل‌ها
SendDateTime	اختیاری	UnixTime	زمان ارسال پیامک (در صورت خالی بودن، ارسال در لحظه انجام می‌شود)
مدل دیتای بازگشتی

مشخصه	نوع	توضیح
PackId	Guid	شناسه یکتای مجموعه ارسال
MessageIds	Array of Integer	آرایه ای از شناسه های یکتای هر پیامک
Cost	Decimal	اعتبار مصرفی مجموعه ارسال
Request Body
{
    "lineNumber": "30004505000017",
    "messageTexts": [
        "سرویس پیامکی ایده پردازان با بیش از یک دهه سابقه همراه شماست",
        "ipdemy.ir  پلتفرم آموزش آنلاین، آکادمی ایده پردازان"
    ],
    "mobiles": [
        "912xxxx677",
        "+98919xxxx904"
    ]
}
Response Body
{
    "status": 1,
    "message": "موفق",
    "data": {
        "packId": "2b99e63c-9bf8-4a21-9bfe-3f72dc1b46f1",
        "messageIds": [
            86522023,
            86522024
        ],
        "cost": 2.0
    }
}



<!-- نمونه کد -->

conn = http.client.HTTPSConnection("api.sms.ir")
payload = json.dumps({
"lineNumber": 300000000000,
"messageTexts": [
    "Your Text 1",
    "Your Text 2"
],
"mobiles": [
    "Your Mobile 1",
    "Your Mobile 1"
],
"senddatetime": None
})
headers = {
'Content-Type': 'application/json',
'Accept': 'text/plain',
'X-API-KEY': 'YOURAPIKEY'
}
conn.request("POST", "/v1/send/likeToLike", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
    

-------------------------
<!-- - ارسال گروهی -->
این متد برای ارسال یک متن پیامک به گروهی از شماره موبایل ها مورد استفاده قرار میگیرد. همچنین شما می‌توانید با مقداردهی به پارامتر زمان ارسال، از قابلیت ارسال پیامک زمانبندی شده نیز استفاده نمایید.

URL

https://api.sms.ir/v1/send/bulk
Request Method
POST
حداکثر تعداد مجاز شماره‌های مقصد 100 می‌باشد.

برای ارسال زمانبندی شده، انتخاب زمان گذشته نامعتبر می‌باشد.

برای ارسال زمانبندی شده، زمان معتبر می‎‌تواند در بازه یک ساعت آینده تا حداکثر 365 روز آینده در نظر گرفته شود.

پارامترهای بدنه درخواست

مشخصه	ارسال	نوع	توضیح
lineNumber	اجباری	Long	شماره خط ارسالی
MessageText	اجباری	String	متن پیام کوتاه
Mobiles	اجباری	Array of String	شماره موبایل‌ها
SendDateTime	اختیاری	UnixTime	زمان ارسال پیامک (در صورت خالی بودن، ارسال در لحظه انجام می‌شود)
مدل دیتای بازگشتی

مشخصه	نوع	توضیح
PackId	Guid	شناسه یکتای مجموعه ارسال
MessageIds	Array of Integer	آرایه ای از شناسه های یکتای هر پیامک
Cost	Decimal	اعتبار مصرفی مجموعه ارسال
Request Body
{
    "lineNumber": 30004505000017,
    "messageText": "سرویس پیامکی ایده پردازان با بیش از یک دهه سابقه همراه شماست",
    "mobiles": [
        "00912xxxx677",
          "0919xxxx904"
    ]
}
Response Body
{
    "status": 1,
    "message": "موفق",
    "data": {
        "packId": "2b99e63c-9bf8-4a21-9bfe-3f72dc1b46f1",
        "messageIds": [
            86522023,
            86522024
        ],
        "cost": 2.0
    }
}
نمونه کد




      conn = http.client.HTTPSConnection("api.sms.ir")
      payload = json.dumps({
        "lineNumber": 300000000000,
        "messageText": "Your Text",
        "mobiles": [
          "Your Mobile 1",
          "Your Mobile 2"
        ],
        "sendDateTime": None
      })
      headers = {
        'X-API-KEY': 'YOURAPIKEY',
        'Content-Type': 'application/json'
      }
      conn.request("POST", "/v1/send/bulk", payload, headers)
      res = conn.getresponse()
      data = res.read()
      print(data.decode("utf-8"))

----------------

<!-- - ارسال VERIFY -->
با استفاده از این متد شما قادر به ارسال پیامک به منظور ارسال کد اعتبارسنجی (verification code)، کد تایید، فاکتور خرید و به طور کلی پیامک‌هایی با اولویت بالا و پارامترهای پویا می‌باشید. از آنجایی که این نوع از ارسال با خطوط خدماتی ارسال میشود امکان دریافت آن توسط افرادی که پیامک‌های تبلیغاتی خود را مسدود کرده‌اند نیز وجود دارد و با اولویت بالایی ارسال خواهد شد.برای استفاده از این نوع ارسال ابتدا قالب پیامک خود را در پنل (بخش ارسال سریع) مشخص نمایید.

URL

https://api.sms.ir/v1/send/verify
Request Method
POST
پارامترهای بدنه درخواست

مشخصه	ارسال	نوع	توضیح
Mobile	اجباری	String	شماره موبایل
TemplateId	اجباری	Integer	شناسه قالب (قالب ها از طریق پنل قابل تعریف و مدیریت می‌باشند)
Parameters	اجباری	Array of Parameter Model	آرایه ای از مدل parameter برای تعیین مقادیر جایگزین شونده در قالب تعریف شده (ساختار مدل parameter در جدول زیر ذکر شده است)
مدل Parameter

مشخصه	ارسال	نوع	توضیح
Name	اجباری	String	کلید تعیین شده در قالب (بدون در نظر گرفتن # در ابتدا و انتهای آن)
Value	اجباری	String	مقدار کلید تعیین شده برای جایگزینی در قالب پیامک (حداکثر 25 کاراکتر)
مدل دیتای بازگشتی

مشخصه	نوع	توضیح
MessageId	Integer	شناسه یکتای پیامک
Cost	Decimal	اعتبار مصرفی ارسال
Request Body
{
    "mobile": "919xxxx904",
    "templateId": 123456,
    "parameters": [
      {
        "name": "Code",
        "value": "12345"
      }
    ]
}
Response Body
{
    "status": 1,
    "message": "موفق",
    "data": {
        "messageId": 89545112,
        "cost": 1.0
    }
}



نمونه کد
conn = http.client.HTTPSConnection("api.sms.ir")
payload = "{\n  \"mobile\": \"Your Mobile\",\n  \"templateId\": YourTemplateID,\n
\"parameters\": [\n    {\n      \"name\": \"PARAMETER1\",\n      \"value\": \"000000\"\n    },
\n    {\n        \"name\":\"PARAMETER2\",\n        \"value\":\"000000\"\n    }\n  ]\n}"
headers = {
'Content-Type': 'application/json',
'Accept': 'text/plain',
'x-api-key': 'YOURAPIKEY'
}
conn.request("POST", "/v1/send/verify", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
