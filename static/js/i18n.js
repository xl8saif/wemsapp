/* WEMS offline bilingual UI switcher.
   Visible UI is translated in both directions. Database values and business
   logic remain unchanged. The translator works on text nodes, attributes,
   form controls, dynamic content and content added after page load.
*/
(function () {
  const U = {
    'ورق انٹرپرائزز مینجمنٹ سسٹم': 'Waraq Enterprises Management System',
    'ورق انٹرپرائز مینجمنٹ سسٹم': 'Waraq Enterprises Management System',
    'ورق انٹرپرائزز': 'Waraq Enterprises',
    'ورق انٹرپرائزز، گلگت کا منصوبہ': 'A project of Waraq Enterprises, Gilgit',
    'ڈویلپر کا تعارف': 'About the Developer',
    'لنکڈ ان سے تازہ': 'Recent from LinkedIn',
    'لنکڈ ان پوسٹس منظم کریں': 'Manage LinkedIn posts',
    'شامل کریں': 'Add',
    'لنکڈ ان پر پوسٹ کھولیں → سب سے اوپر … مینو → "Copy link to post" → یہاں پیسٹ کریں۔ زیادہ سے زیادہ 4 پوسٹس۔': 'Open the post on LinkedIn → top-right … menu → "Copy link to post" → paste here. Up to 4 posts.',
    'لنکڈ ان پوسٹ شامل ہو گئی۔ LinkedIn post added.': 'LinkedIn post added.',
    'لنکڈ ان پوسٹ ہٹا دی گئی۔ LinkedIn post removed.': 'LinkedIn post removed.',
    'یہ لنکڈ ان پوسٹ کا لنک نہیں۔ LinkedIn post link required.': 'That is not a LinkedIn post link. Please paste a LinkedIn post URL.',
    'صارفین': 'Users', 'نیا صارف شامل کریں': 'Add New User', 'صارف نام': 'Username', 'پورا نام': 'Full Name',
    'کردار': 'Role', 'ایڈمین': 'Admin', 'عملہ': 'Staff', 'فعال': 'Active', 'بند': 'Disabled', 'بند کریں': 'Disable', 'چالو کریں': 'Enable',
    'پاس ورڈ ری سیٹ': 'Reset Password', 'نیا پاس ورڈ': 'New Password', 'موجودہ پاس ورڈ': 'Current Password',
    'پاس ورڈ تبدیل کریں': 'Change Password', 'نیا پاس ورڈ دوبارہ': 'Confirm New Password', 'پاس ورڈ دوبارہ': 'Confirm Password',
    'پاس ورڈ کم از کم 6 حروف کا ہونا چاہیے۔': 'Password must be at least 6 characters.',
    'پاس ورڈز مشابہ نہیں ہیں۔': 'Passwords do not match.',
    'یہ صارف نام پہلے سے موجود ہے۔': 'Username already exists.',
    'غلط صارف نام یا پاس ورڈ۔': 'Invalid username or password.',
    'ایڈمین اکاؤنٹ بنا دیا گیا۔ اب داخل ہوں۔': 'Admin account created. Please sign in.',
    'ابتدائی ترتیب': 'Initial Setup', 'ایکاؤنٹ بنائیں': 'Create Account',
    '(آپ)': '(you)', 'اپ لوڈز': 'Uploads',
    'پروفائل': 'Profile', 'میری پروفائل': 'My Profile', 'پروفائل دیکھیں': 'View Profile', 'پروفائل میں ترمیم': 'Edit Profile',
    'صارف پروفائل': 'User Profile', 'ذاتی پروفائل': 'Personal Profile',
    'پورا نام': 'Full Name', 'ای میل': 'Email', 'تاریخِ پیدائش': 'Date of Birth', 'موبائل نمبر': 'Mobile Number',
    'سوشل میڈیا': 'Social Media', 'ہنر': 'Skills', 'ہنر کا انتخاب کریں': 'Select Skills', 'سی وی اپ لوڈ کریں': 'Upload CV',
    'تعارف': 'Summary', 'سوانح حیات': 'CV / Resume', 'ڈاؤن لوڈ کریں': 'Download', 'تصویر اپ لوڈ کریں': 'Upload Photo',
    'محفوظ پروفائل': 'Save Profile', 'صرف تصویری فائلیں (PNG، JPG، WEBP) تصویر کے لیے جائز ہیں۔': 'Only image files (PNG, JPG, WEBP) are allowed for the photo.',
    'صرف پی ڈی ایف یا ورڈ دستاویز سی وی کے لیے جائز ہے۔': 'Only PDF or Word documents are allowed for the CV.',
    'ہنر منتخب نہیں کیا گیا۔': 'No skills selected yet.', 'سوشل ہینڈل درج نہیں۔': 'No social handles added yet.',
    'کلاؤڈ ٹرانس کی تکنیکی معاونت — ڈیجیٹل حل کا معروف پلیٹ فارم': 'Technical Assistance of CloudTrans — a leading digital solutions platform',
    'ورق انٹرپرائزز، گلگت': 'Waraq Enterprises, Gilgit',
    'ورق انٹرپرائزز، گلگت — WEMS v1.0': 'Waraq Enterprises, Gilgit — WEMS v1.0',
    'سید سیف اللہ جیلانی': 'Saif Ullah Jailani',
    'اردو کیلکولیٹر': 'Urdu Calculator', 'سائٹ وزٹرز:': 'Site visitors:', 'روزمرہ حساب کے لیے سادہ، تیز اور موبائل فرینڈلی کیلکولیٹر۔ اعداد اردو ہندسوں میں دکھائے جاتے ہیں۔': 'A simple, fast and mobile-friendly calculator for everyday calculations. Numbers are displayed in Urdu digits.', 'جمع، تفریق، ضرب، تقسیم اور فیصد': 'Addition, subtraction, multiplication and percentage', 'کی بورڈ سے بھی اعداد اور بنیادی آپریٹرز استعمال کیے جا سکتے ہیں': 'Numbers and basic operators can also be entered from the keyboard', 'AC سے حساب صاف کریں اور ⌫ سے آخری ہندسہ حذف کریں': 'Use AC to clear the calculation and ⌫ to delete the last digit', 'ڈیش بورڈ': 'Dashboard', 'کلائنٹس': 'Clients', 'کلائنٹ': 'Client',
    'کلائنٹ پروفائل': 'Client Profile', 'کلائنٹ کی معلومات': 'Client Information',
    'کلائنٹ کا نام': 'Client Name', 'کلائنٹ کا نام *': 'Client Name *', 'کلائنٹ کی قسم': 'Client Type',
    'کام اور خدمات': 'Jobs & Services', 'کام': 'Jobs', 'کام کی تفصیلات': 'Job Details', 'کام کی معلومات': 'Job Information',
    'نیا کام': 'New Job', 'کام میں ترمیم': 'Edit Job', 'کام کا عنوان': 'Job Title', 'کام کا عنوان *': 'Job Title *',
    'خدمات': 'Services', 'خدمت': 'Service', 'خدمت کی تفصیلات': 'Service Details', 'خدمت کا نام': 'Service Name',
    'خدمات کا کیٹلاگ': 'Service Catalog', 'نئی خدمت شامل کریں': 'Add New Service', 'خدمت میں ترمیم': 'Edit Service',
    'انوائسز': 'Invoices', 'انوائس': 'Invoice', 'انوائس کی تفصیلات': 'Invoice Details', 'نئی انوائس': 'New Invoice',
    'نئی انوائس بنائیں': 'Create New Invoice', 'انوائس کی اشیاء': 'Invoice Items', 'انوائس بنائیں': 'Create Invoice',
    'ادائیگیاں': 'Payments', 'ادائیگی': 'Payment', 'ادائیگی کی تفصیلات': 'Payment Details',
    'ادائیگیوں کا ریکارڈ': 'Payment Records', 'ادائیگی درج کریں': 'Record Payment', 'ادائیگیوں کی تاریخ': 'Payment History',
    'رپورٹس': 'Reports', 'کاروباری رپورٹس': 'Business Reports', 'ڈیٹا بیس بیک اَپ': 'Database Backup',
    'تلاش': 'Search', 'تلاش کریں': 'Search', 'صاف کریں': 'Clear', 'شامل کریں': 'Add',
    'کلائنٹ شامل کریں': 'Add Client', 'خدمت شامل کریں': 'Add Service', 'شے شامل کریں': 'Add Item',
    'محفوظ کریں': 'Save', 'اپ ڈیٹ کریں': 'Update', 'منسوخ کریں': 'Cancel', 'ترمیم': 'Edit', 'حذف': 'Delete',
    'دیکھیں': 'View', 'سب دیکھیں': 'View All', 'کارروائیاں': 'Actions', 'پرنٹ': 'Print', 'پرنٹ منظر': 'Print View',
    'پی ڈی ایف': 'PDF', 'پی ڈی ایف محفوظ کریں': 'Save PDF', 'انوائس پرنٹ کریں': 'Print Invoice',
    'کلائنٹس تلاش کریں۔۔۔': 'Search clients...', 'کام تلاش کریں۔۔۔': 'Search jobs...', 'انوائسز تلاش کریں۔۔۔': 'Search invoices...',
    'شناختی نمبر': 'ID', 'شناختی کارڈ / شناختی نمبر': 'CNIC / ID Number', 'نام': 'Name', 'رابطہ فرد': 'Contact Person',
    'فون': 'Phone', 'فون نمبر': 'Phone Number', 'ای میل': 'Email', 'پتہ': 'Address', 'قسم': 'Type',
    'تمام اقسام': 'All Types', 'فرد': 'Individual', 'کاروباری ادارہ': 'Business', 'سرکاری ادارہ': 'Government',
    'زمرہ': 'Category', 'تمام زمرے': 'All Categories', 'قانونی مسودہ نویسی': 'Legal Drafting',
    'عدالتی خدمات': 'Court Services', 'طباعت': 'Printing', 'آن لائن رجسٹریشن': 'Online Registration',
    'دستاویزی خدمات': 'Documentation Services', 'دیگر': 'Other',
    'حیثیت': 'Status', 'تمام حیثیتیں': 'All Statuses', 'ادا شدہ': 'Paid', 'غیر ادا شدہ': 'Unpaid',
    'جزوی ادائیگی': 'Partially Paid', 'زیرِ التوا': 'Pending', 'جاری ہے': 'In Progress', 'مکمل': 'Completed', 'منسوخ': 'Cancelled',
    'ترجیح': 'Priority', 'کم': 'Low', 'معمول': 'Normal', 'زیادہ': 'High', 'فوری': 'Urgent',
    'لاگت': 'Cost', 'تخمینی لاگت': 'Estimated Cost', 'آخری تاریخ': 'Due Date', 'آغاز کی تاریخ': 'Start Date',
    'ادائیگی کی آخری تاریخ': 'Payment Due Date', 'تکمیل کی تاریخ': 'Completion Date', 'ذمہ دار فرد': 'Assigned To',
    'متعین نہیں': 'Not assigned', 'مقرر نہیں': 'Not set', 'ابھی مکمل نہیں ہوا': 'Not completed yet', 'بنایا گیا': 'Created',
    'تفصیل': 'Description', 'نوٹس': 'Notes', 'ٹائم لائن': 'Timeline', 'تاریخ': 'Date', 'اجراء': 'Issued', 'اجراء کی تاریخ': 'Issue Date',
    'انوائس نمبر': 'Invoice Number', 'متعلقہ کام': 'Related Job', 'کل': 'Total', 'مقدار': 'Quantity',
    'فی یونٹ قیمت': 'Unit Price', 'رقم': 'Amount', 'ذیلی مجموعہ:': 'Subtotal:', 'ٹیکس:': 'Tax:', 'ٹیکس (0٪):': 'Tax (0%):',
    'رعایت:': 'Discount:', 'کل رقم:': 'Total Amount:', 'ادا شدہ:': 'Paid:', 'قابلِ ادائیگی بقایا:': 'Balance Due:',
    'بقایا': 'Outstanding', 'کل بل شدہ': 'Total Billed', 'کل ادا شدہ': 'Total Paid', 'موصول شدہ': 'Collected',
    'موصول شدہ ادائیگیاں': 'Payments Received', 'کل آمدن': 'Total Revenue', 'بقایا جات': 'Outstanding Balances',
    'آمدن کا جائزہ': 'Revenue Overview', 'حالیہ کام': 'Recent Jobs', 'حالیہ انوائسز': 'Recent Invoices', 'آمدن': 'Revenue',
    'وصول شدہ': 'Collected', 'ادائیگی کی تاریخ': 'Payment Date', 'طریقۂ ادائیگی': 'Payment Method', 'نقد': 'Cash',
    'بینک ٹرانسفر': 'Bank Transfer', 'چیک': 'Cheque', 'آن لائن': 'Online', 'حوالہ نمبر': 'Reference Number', 'حوالہ': 'Reference',
    'کلائنٹس برآمد کریں': 'Export Clients', 'انوائسز برآمد کریں': 'Export Invoices', 'کام برآمد کریں': 'Export Jobs',
    'زمرے کے لحاظ سے آمدن': 'Revenue by Category', 'ماہانہ خلاصہ': 'Monthly Summary', 'ماہ': 'Month', 'اخراجات کا خلاصہ': 'Expense Summary',
    'کل رقم': 'Total Amount', 'کل کلائنٹس': 'Total Clients', 'کل کام': 'Total Jobs', 'کل انوائسز': 'Total Invoices',
    'غیر ادا شدہ انوائسز': 'Unpaid Invoices', 'زیرِ التوا کام': 'Pending Jobs',
    'کوئی کلائنٹ نہیں ملا۔': 'No clients found.', 'کوئی کام نہیں ملا۔': 'No jobs found.', 'کوئی انوائس نہیں ملی۔': 'No invoices found.',
    'ابھی کوئی کام موجود نہیں۔': 'No jobs yet.', 'ابھی کوئی انوائس موجود نہیں۔': 'No invoices yet.',
    'ابھی کوئی ادائیگی درج نہیں کی گئی۔': 'No payments recorded yet.', 'ابھی کوئی خدمت ترتیب نہیں دی گئی۔': 'No services configured yet.',
    'اس کلائنٹ کے لیے کوئی کام موجود نہیں۔': 'No jobs found for this client.', 'اس کلائنٹ کے لیے کوئی انوائس موجود نہیں۔': 'No invoices found for this client.',
    'اس وقت کوئی بقایا رقم موجود نہیں۔': 'No outstanding balance at this time.', 'دستیاب نہیں': 'Not available',
    'کوئی تفصیل فراہم نہیں کی گئی۔': 'No description provided.', 'کوئی تفصیل موجود نہیں۔': 'No description available.', 'کوئی نوٹس نہیں۔': 'No notes.',
    'آپ کے کاروبار کا شکریہ۔': 'Thank you for your business.',
    'کیا آپ اس کلائنٹ کو حذف کرنا چاہتے ہیں؟': 'Are you sure you want to delete this client?',
    'کیا آپ اس کام کو حذف کرنا چاہتے ہیں؟': 'Are you sure you want to delete this job?',
    'کیا آپ اس انوائس کو حذف کرنا چاہتے ہیں؟': 'Are you sure you want to delete this invoice?',
    'کیا آپ اس خدمت کو حذف کرنا چاہتے ہیں؟': 'Are you sure you want to delete this service?',
    'کلائنٹ کامیابی سے شامل کر دیا گیا۔': 'Client added successfully.', 'کلائنٹ کی معلومات کامیابی سے اپ ڈیٹ کر دی گئیں۔': 'Client information updated successfully.',
    'کلائنٹ کامیابی سے حذف کر دیا گیا۔': 'Client deleted successfully.', 'سروس کامیابی سے شامل کر دی گئی۔': 'Service added successfully.',
    'سروس کامیابی سے اپ ڈیٹ کر دی گئی۔': 'Service updated successfully.', 'سروس کامیابی سے حذف کر دی گئی۔': 'Service deleted successfully.',
    'کام کامیابی سے بنا دیا گیا۔': 'Job created successfully.', 'کام کامیابی سے اپ ڈیٹ کر دیا گیا۔': 'Job updated successfully.',
    'کام کامیابی سے حذف کر دیا گیا۔': 'Job deleted successfully.', 'ادائیگی کامیابی سے درج کر دی گئی۔': 'Payment recorded successfully.',
    'انوائس کامیابی سے حذف کر دی گئی۔': 'Invoice deleted successfully.', 'پی ڈی ایف تیار کرتے وقت خرابی پیش آئی۔': 'Error generating PDF.',
    'تیار کردہ:': 'Developed by:', 'تیار کردہ': 'Developed by', 'ویب سائٹ': 'Website', 'پروفائل': 'Profile', 'مینو کھولیں': 'Open menu', 'مینو بند کریں': 'Close menu',
    'سینئر مترجم، لوکلائزیشن اسپیشلسٹ اور لینگویج ٹیکنالوجی ماہر': 'Senior Translator, Localization Specialist & Language Technology Expert',
    '12+ سالہ پیشہ ورانہ تجربہ، 3,500+ منصوبے؛ قانونی، مذہبی، کارپوریٹ، تکنیکی، تعلیمی، میڈیکل، حکومتی اور گیم لوکلائزیشن میں ترجمہ، MTPE، LQA، لسانی جانچ اور کثیر لسانی مواد کی تیاری۔ اردو مادری زبان؛ عربی، فارسی، انگریزی اور علاقائی زبانوں میں عملی مہارت، بشمول انڈس کوہستانی اور شینا۔': '12+ years of professional experience across 3,500+ projects: translation, MTPE, LQA, linguistic testing and multilingual content preparation in legal, religious, corporate, technical, educational, medical, government and game localization. Native Urdu; working proficiency in Arabic, Persian, English and regional languages including Indus Kohistani and Shina.',
    'ورق انٹرپرائزز، کورٹ ایریا، یونیورسٹی روڈ، کونوداس، گلگت، پاکستان': 'Waraq Enterprises, Court Area, University Road, Konodas, Gilgit, Pakistan',
    '-- کوئی نہیں --': '-- None --', '-- کلائنٹ منتخب کریں --': '-- Select Client --', '-- خدمت منتخب کریں --': '-- Select Service --',
    'انوائس {{': 'Invoice {{',
    'اخراجات': 'Expenses', 'دفتری اخراجات': 'Office Expenses', 'خرچ': 'Expense',
    'خرچ شامل کریں': 'Add Expense', 'نیا خرچ شامل کریں': 'Add New Expense',
    'اس ماہ کے اخراجات': 'This Month Expenses', 'کل اخراجات': 'Total Expenses',
    'ادا کرنے والا': 'Paid By', 'فلٹر کریں': 'Filter', 'لاگ آؤٹ': 'Logout',
    'پاس ورڈ': 'Password', 'داخل ہوں': 'Sign In', 'لاگ ان': 'Login',
    'ابھی کوئی خرچ درج نہیں ہوا۔': 'No expenses recorded yet.',
    'کیا آپ یہ خرچ حذف کرنا چاہتے ہیں؟': 'Are you sure you want to delete this expense?',
    'محفوظ دفتری نظام — براہِ کرم پاس ورڈ درج کریں': 'Secure office system — please enter your password',
    'مثلاً: کرایہ، کاغذات، ٹرانسپورٹ': 'e.g., Rent, Stationery, Transport',
    'غلط پاس ورڈ۔ دوبارہ کوشش کریں۔ Invalid password.': 'Invalid password. Please try again.',
    'خرچ کامیابی سے شامل کر دیا گیا۔': 'Expense added successfully.',
    'خرچ کامیابی سے حذف کر دیا گیا۔': 'Expense deleted successfully.',
    'خرچ کا زمرہ لازمی ہے۔': 'Expense category is required.',
    'خرچ کی رقم مثبت ہونی چاہیے۔': 'Expense amount must be a positive number.',
    'ادائیگی کی رقم مثبت ہونی چاہیے۔': 'Payment amount must be a positive number.',
    'براہِ کرم کلائنٹ منتخب کریں۔': 'Please select a client.',
    'کلائنٹ کا نام لازمی ہے۔': 'Client name is required.',
    'کلائنٹ اور کام کا عنوان لازمی ہے۔': 'Client and job title are required.',
    'خدمت کا نام اور زمرہ لازمی ہے۔': 'Service name and category are required.',
    'انوائس نہیں ملی۔': 'Invoice not found.',
    'اس کلائنٹ کے انوائسز موجود ہیں، اس لیے حذف نہیں کیا جا سکتا۔ پہلے ان کے انوائسز حذف یا دوبارہ منتقل کریں۔': 'This client has invoices and cannot be deleted. Delete or reassign their invoices first.',
    'اس کلائنٹ کے کام موجود ہیں، اس لیے حذف نہیں کیا جا سکتا۔ پہلے اس کے کام حذف کریں۔': 'This client has jobs and cannot be deleted. Delete their jobs first.',
    'اس کام کی انوائسز منسلک ہیں، اس لیے حذف نہیں کیا جا سکتا۔': 'This job has invoices linked to it and cannot be deleted.',
    'اس انوائس کے خلاف ادائیگیاں درج ہیں، اس لیے حذف نہیں کی جا سکتی۔ پہلے ادائیگیاں حذف کریں۔': 'This invoice has payments recorded and cannot be deleted. Delete its payments first.',
    'لاگ ان — WEMS': 'Login — WEMS',
    'ورق انٹرپرائزز، گلگت کا منصوبہ': 'A project of Waraq Enterprises, Gilgit',
    'محفوظ دفتری نظام — صارف نام اور پاس ورڈ درج کریں': 'Secure office system — enter your username and password',
    'محفوظ دفتری نظام — براہِ کرم پاس ورڈ درج کریں': 'Secure office system — please enter your password',
    'ابتدائی ترتیب — پہلا ایڈمین اکاؤنٹ بنائیں': 'Initial Setup — Create the First Admin Account',
    'یہ صفحہ صرف پہلے اکاؤنٹ کے لیے ہے — بعد میں ایڈمین مزید صارفین بنائے گا': 'This page is only for the first account — the admin can create additional users afterward',
    'پاس ورڈ (کم از کم 6 حروف)': 'Password (minimum 6 characters)',
    'موجودہ تصویر محفوظ ہے — نئی اپ لوڈ اسے بدل دے گی۔': 'The current photo is saved — a new upload will replace it.',
    'موجودہ:': 'Current:',
    'سوشل میڈیا (لنک یا آئی ڈی — ہٹا نہیں سکتے، صرف شامل کریں)': 'Social media (link or ID — existing entries cannot be removed, only added)',
    'ہنر کا انتخاب کریں': 'Select Skills',
    'تعارف (مختصر)': 'Summary (brief)',
    'اپنے بارے میں دو چار جملے...': 'Write two or three sentences about yourself...',
    'سوانح حیات ڈاؤن لوڈ کریں': 'Download CV / Resume',
    'سوانح حیات اپ لوڈ نہیں کی گئی۔': 'No CV / Resume uploaded.',
    'نیا عملہ صارف شامل کریں': 'Add New Staff User',
    'صرف ایڈمن صارفین بنا سکتا ہے۔ نئے اکاؤنٹس صرف عملہ (staff) کردار کے ساتھ بنیں گے؛ عوامی رجسٹریشن دستیاب نہیں۔': 'Only an admin can create users. New accounts are created only with the staff role; public registration is not available.',
    'صارفین (': 'Users (',
    'پاس ورڈ تبدیل کریں': 'Change Password',
    'ہر صارف پہلی بار داخل ہونے کے بعد': 'After signing in for the first time, each user can',
    'میری پروفائل': 'My Profile',
    'پروفائل سنوار سکتا ہے۔': 'update their profile.',
    'خرچ کا زمرہ لازمی ہے۔': 'Expense category is required.',
    'خرچ کی رقم مثبت ہونی چاہیے۔': 'Expense amount must be a positive number.',
    'اس ماہ کے اخراجات': 'This Month Expenses',
    'نیا خرچ شامل کریں': 'Add New Expense',
    'کیا آپ یہ خرچ حذف کرنا چاہتے ہیں؟': 'Are you sure you want to delete this expense?',
    'مثلاً: کرایہ، کاغذات، ٹرانسپورٹ': 'e.g., Rent, stationery, transport',
    'ادا کرنے والا': 'Paid By',
    'زمرے کے لحاظ سے آمدن': 'Revenue by Category',
    'ماہانہ خلاصہ': 'Monthly Summary',
    'اخراجات کا خلاصہ': 'Expense Summary',
    'انوائسز (': 'Invoices (',
    'کام (': 'Jobs (',
    'کسٹم کام': 'Custom Job',
    'ادائیگی درج کریں': 'Record Payment',
    'ادائیگیوں کی تاریخ': 'Payment History',
    'بل برائے': 'Bill To',
    'مجاز دستخط': 'Authorized Signature',
    'ادارے کی مہر': 'Company Stamp',
    'ورق انٹرپرائزز کے مجاز دستخط': 'Authorized signature of Waraq Enterprises',
    'ورق انٹرپرائزز کی مہر': 'Company stamp of Waraq Enterprises',
    'CloudTrans کے تعاون سے': 'Powered by CloudTrans',
    'سروس': 'Service',
    'بنیادی قیمت': 'Base Price',
    'خدمت سے انتخاب کریں': 'Choose from Services',
    'کوئی سروس موجود نہیں — براہِ کرم دستی طور پر لکھیں': 'No services available — please enter manually',
    'کلائنٹ منتخب کریں': 'Select Client',
    'خدمت منتخب کریں': 'Select Service',
    'صارف پروفائل': 'User Profile',
    'ذاتی پروفائل': 'Personal Profile',
    'نام درج کریں': 'Enter Name',
    'موجودہ پاس ورڈ': 'Current Password',
    'نیا پاس ورڈ (کم از کم 6 حروف)': 'New Password (minimum 6 characters)',
    'نیا پاس ورڈ (12+)': 'New Password (12+)',
    'صارف نام اور پاس ورڈ درج کریں': 'Enter username and password',
    'پہلا ایڈمین اکاؤنٹ بنائیں': 'Create the First Admin Account',
    'ایکاؤنٹ بنائیں': 'Create Account',
    'مینو بند کریں': 'Close menu',
    'ہٹانا ہے؟ Remove this post?': 'Remove this post?',
    'ہٹائیں / Remove': 'Remove',
    'ابھی کوئی پوسٹ پن نہیں کی گئی۔': 'No posts pinned yet.',
    'ہٹانا ہے؟': 'Remove?',
    'خدمات سے انتخاب کریں': 'Choose from Services',
    'کوئی سروس موجود نہیں — براہِ کرم دستی طور پر لکھیں': 'No services available — please enter manually',
    'خدمت سے انتخاب کریں': 'Choose from Service',
    'نئی خدمت شامل کریں': 'Add New Service',
    'نئی انوائس بنائیں': 'Create New Invoice',
    'نئی انوائس': 'New Invoice',
    'دفتری اخراجات': 'Office Expenses',
    'خرچ شامل کریں': 'Add Expense',
    'کل اخراجات': 'Total Expenses',
    'فلٹر کریں': 'Filter',
    'مجاز دستخط': 'Authorized Signature',
    'ادارے کی مہر': 'Company Stamp',
    'بل برائے': 'Bill To',
    'قابلِ ادائیگی بقایا:': 'Balance Due:',
    'جزوی ادائیگی': 'Partially Paid',
    'ادا شدہ': 'Paid',
    'کلائنٹ اور کام کا عنوان لازمی ہے۔': 'Client and job title are required.',
    'خدمت کا نام اور زمرہ لازمی ہے۔': 'Service name and category are required.',
    'پروفائل سنوار سکتا ہے۔': 'update their profile.',
    'پہلا ایڈمین اکاؤنٹ بنائیں': 'Create the First Admin Account',
    'یہ صفحہ صرف پہلے اکاؤنٹ کے لیے ہے — بعد میں ایڈمین مزید صارفین بنائے گا': 'This page is only for the first account — the admin can create additional users afterward',
    'محفوظ دفتری نظام — صارف نام اور پاس ورڈ درج کریں': 'Secure office system — enter your username and password',
    'موجودہ تصویر محفوظ ہے — نئی اپ لوڈ اسے بدل دے گی۔': 'The current photo is saved — a new upload will replace it.',
    'سوشل میڈیا (لنک یا آئی ڈی — ہٹا نہیں سکتے، صرف شامل کریں)': 'Social media (link or ID — existing entries cannot be removed, only added)',
    'تعارف (مختصر)': 'Summary (brief)',
    'اپنے بارے میں دو چار جملے...': 'Write two or three sentences about yourself...',
    'ہنر منتخب نہیں کیا گیا۔': 'No skills selected yet.',
    'سوانح حیات اپ لوڈ نہیں کی گئی۔': 'No CV / Resume uploaded.',
    'موجودہ:': 'Current:',
    'نیا عملہ صارف شامل کریں': 'Add New Staff User',
    'صرف ایڈمن صارفین بنا سکتا ہے۔ نئے اکاؤنٹس صرف عملہ (staff) کردار کے ساتھ بنیں گے؛ عوامی رجسٹریشن دستیاب نہیں۔': 'Only an admin can create users. New accounts are created only with the staff role; public registration is not available.',
    'پاس ورڈ (کم از کم 6 حروف)': 'Password (minimum 6 characters)',
    'پاس ورڈ (12+)': 'Password (12+)',
    'صارفین (': 'Users (',
    'انوائسز (': 'Invoices (',
    'کام (': 'Jobs (',
    'مینو کھولیں': 'Open menu',
  };

  const E = Object.fromEntries(Object.entries(U).map(([u, e]) => [e, u]));
  const urPairs = Object.entries(U).sort((a, b) => b[0].length - a[0].length);
  const enPairs = Object.entries(E).sort((a, b) => b[0].length - a[0].length);

  function translateValue(value, lang) {
    if (!value) return value;
    let out = String(value);
    const pairs = lang === 'en' ? urPairs : enPairs;
    pairs.forEach(([from, to]) => {
      if (out.includes(from)) out = out.split(from).join(to);
    });

    if (lang === 'en') {
      out = out.replace(/انوائس\s+(.+?)\s+کامیابی سے بنا دی گئی۔/g, 'Invoice $1 created successfully.');
      out = out.replace(/ڈیٹا بیس کا بیک اَپ کامیابی سے بنا دیا گیا۔/g, 'Database backup created successfully.');
    } else {
      out = out.replace(/Invoice\s+(.+?)\s+created successfully\./g, 'انوائس $1 کامیابی سے بنا دی گئی۔');
      out = out.replace(/Database backup created successfully\./g, 'ڈیٹا بیس کا بیک اَپ کامیابی سے بنا دیا گیا۔');
    }
    return out;
  }

  function translateTextNode(node, lang) {
    if (!node.nodeValue || !node.nodeValue.trim()) return;
    const parent = node.parentElement;
    if (!parent || ['SCRIPT', 'STYLE', 'NOSCRIPT'].includes(parent.tagName)) return;
    node.nodeValue = translateValue(node.nodeValue, lang);
  }

  function translateElementAttributes(el, lang) {
    ['placeholder', 'title', 'aria-label', 'value', 'alt'].forEach(attr => {
      if (el.hasAttribute(attr)) {
        const old = el.getAttribute(attr);
        const next = translateValue(old, lang);
        if (next !== old) el.setAttribute(attr, next);
      }
    });
  }

  let translating = false;
  function translate(lang) {
    if (translating) return;
    translating = true;
    const isEnglish = lang === 'en';
    document.documentElement.lang = isEnglish ? 'en' : 'ur';
    document.documentElement.dir = isEnglish ? 'ltr' : 'rtl';
    document.body.classList.toggle('wems-english', isEnglish);

    document.querySelectorAll('[data-lang-label]').forEach(el => {
      el.textContent = isEnglish ? 'اردو' : 'English';
    });

    document.title = translateValue(document.title, lang);

    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const nodes = [];
    let node;
    while ((node = walker.nextNode())) nodes.push(node);
    nodes.forEach(n => translateTextNode(n, lang));
    document.querySelectorAll('input, textarea, select, button, a, [title], [aria-label]').forEach(el => translateElementAttributes(el, lang));

    localStorage.setItem('wems-language', lang);
    // Mirror the choice into a cookie so server-rendered documents
    // (invoice print view / PDF) come out in the same language.
    document.cookie = 'wems-lang=' + lang + ';path=/;max-age=31536000;samesite=strict';
    translating = false;
  }

  function init() {
    const btn = document.getElementById('languageToggle');
    if (btn) btn.addEventListener('click', () => translate(document.documentElement.lang === 'en' ? 'ur' : 'en'));

    const saved = localStorage.getItem('wems-language') || 'ur';
    translate(saved);

    const observer = new MutationObserver(mutations => {
      if (translating) return;
      const lang = document.documentElement.lang || 'ur';
      mutations.forEach(m => {
        m.addedNodes.forEach(n => {
          if (n.nodeType === Node.TEXT_NODE) translateTextNode(n, lang);
          else if (n.nodeType === Node.ELEMENT_NODE) {
            const walker = document.createTreeWalker(n, NodeFilter.SHOW_TEXT);
            const nodes = [];
            let x;
            while ((x = walker.nextNode())) nodes.push(x);
            nodes.forEach(t => translateTextNode(t, lang));
            if (n.matches && n.matches('input, textarea, select, button, a, [title], [aria-label]')) translateElementAttributes(n, lang);
            n.querySelectorAll && n.querySelectorAll('input, textarea, select, button, a, [title], [aria-label]').forEach(el => translateElementAttributes(el, lang));
          }
        });
      });
    });
    observer.observe(document.body, {childList: true, subtree: true});
  }

  document.addEventListener('DOMContentLoaded', init);
})();
