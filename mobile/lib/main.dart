import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

void main() { WidgetsFlutterBinding.ensureInitialized(); runApp(const MolidoCctvApp()); }

const brandRed = Color(0xFFE3262E);
const ink = Color(0xFF101216);
const panel = Color(0xFF1B1F25);

const i18n = <String, Map<String, String>>{
 'fa': {'home':'خانه','cameras':'دوربین‌ها','events':'رخدادها','settings':'تنظیمات','sync':'همگام‌سازی','center':'مرکز نظارت هوشمند','total':'کل دوربین‌ها','online':'آنلاین','alerts':'هشدار امروز','live':'نمای زنده','all':'همه دوربین‌ها','demo':'نسخه آزمایشی: تصویر زنده و تحلیل هوشمند پس از راه‌اندازی سرویس استریم و اتصال واقعی دستگاه فعال می‌شود.','manage':'مدیریت دوربین‌ها','device':'دستگاه','syncing':'در حال همگام‌سازی','syncServer':'همگام‌سازی با سرور','eventTitle':'رخدادها و هشدارها','empty':'هنوز رخدادی دریافت نشده','emptyHelp':'پس از اتصال دوربین‌ها و فعال‌سازی تحلیل، هشدارها اینجا نمایش داده می‌شوند.','appSettings':'تنظیمات برنامه','server':'آدرس سرور مرکزی','language':'زبان','security':'امنیت','credentialNote':'اطلاعات ورود دوربین در این نسخه موبایل ذخیره نمی‌شود.','version':'نسخه','check':'بررسی اتصال به سرور','add':'افزودن دوربین','cameraName':'نام دوربین','host':'IP یا Host','brand':'برند','cancel':'انصراف','save':'ذخیره','local':'حالت آزمایشی محلی','connecting':'در حال اتصال…','connected':'متصل به سرور','unavailable':'سرور در دسترس نیست • حالت آزمایشی','updated':'فهرست دوربین‌ها به‌روزرسانی شد','failed':'اتصال برقرار نشد؛ آدرس سرور و شبکه را بررسی کنید','saved':'دوربین در سرور ثبت شد','localOnly':'فقط در فهرست محلی افزوده شد؛ سرور متصل نیست'},
 'en': {'home':'Home','cameras':'Cameras','events':'Events','settings':'Settings','sync':'Sync','center':'Smart monitoring center','total':'Total cameras','online':'Online','alerts':"Today's alerts",'live':'Live view','all':'All cameras','demo':'Test version: live video and AI analytics will be enabled after the streaming service and real device connection are implemented.','manage':'Camera management','device':'devices','syncing':'Synchronizing…','syncServer':'Sync with server','eventTitle':'Events & alerts','empty':'No events received yet','emptyHelp':'Alerts will appear here after cameras are connected and analytics are enabled.','appSettings':'App settings','server':'Central server address','language':'Language','security':'Security','credentialNote':'Camera login credentials are not stored in this mobile version.','version':'Version','check':'Check server connection','add':'Add camera','cameraName':'Camera name','host':'IP or Host','brand':'Brand','cancel':'Cancel','save':'Save','local':'Local demo mode','connecting':'Connecting…','connected':'Connected to server','unavailable':'Server unavailable • Demo mode','updated':'Camera list updated','failed':'Connection failed; check the server address and network','saved':'Camera saved on server','localOnly':'Added locally only; server is not connected'},
 'ar': {'home':'الرئيسية','cameras':'الكاميرات','events':'الأحداث','settings':'الإعدادات','sync':'مزامنة','center':'مركز المراقبة الذكي','total':'إجمالي الكاميرات','online':'متصل','alerts':'تنبيهات اليوم','live':'العرض المباشر','all':'كل الكاميرات','demo':'نسخة تجريبية: سيتم تفعيل البث المباشر والتحليل الذكي بعد إعداد خدمة البث وربط الأجهزة الفعلية.','manage':'إدارة الكاميرات','device':'أجهزة','syncing':'جارٍ المزامنة…','syncServer':'مزامنة مع الخادم','eventTitle':'الأحداث والتنبيهات','empty':'لا توجد أحداث بعد','emptyHelp':'ستظهر التنبيهات هنا بعد ربط الكاميرات وتفعيل التحليلات.','appSettings':'إعدادات التطبيق','server':'عنوان الخادم المركزي','language':'اللغة','security':'الأمان','credentialNote':'لا يتم حفظ بيانات دخول الكاميرات في إصدار الهاتف هذا.','version':'الإصدار','check':'فحص الاتصال بالخادم','add':'إضافة كاميرا','cameraName':'اسم الكاميرا','host':'عنوان IP أو المضيف','brand':'العلامة التجارية','cancel':'إلغاء','save':'حفظ','local':'وضع تجريبي محلي','connecting':'جارٍ الاتصال…','connected':'متصل بالخادم','unavailable':'الخادم غير متاح • وضع تجريبي','updated':'تم تحديث قائمة الكاميرات','failed':'تعذر الاتصال؛ تحقق من عنوان الخادم والشبكة','saved':'تم حفظ الكاميرا على الخادم','localOnly':'أضيفت محلياً فقط؛ الخادم غير متصل'},
 'tr': {'home':'Ana Sayfa','cameras':'Kameralar','events':'Olaylar','settings':'Ayarlar','sync':'Senkronize et','center':'Akıllı izleme merkezi','total':'Toplam kamera','online':'Çevrimiçi','alerts':'Bugünkü uyarılar','live':'Canlı görüntü','all':'Tüm kameralar','demo':'Test sürümü: canlı video ve yapay zekâ analizi, akış hizmeti ve gerçek cihaz bağlantısı tamamlandığında etkinleşir.','manage':'Kamera yönetimi','device':'cihaz','syncing':'Senkronize ediliyor…','syncServer':'Sunucuyla senkronize et','eventTitle':'Olaylar ve uyarılar','empty':'Henüz olay alınmadı','emptyHelp':'Kameralar bağlanıp analiz etkinleştirildiğinde uyarılar burada görünür.','appSettings':'Uygulama ayarları','server':'Merkezi sunucu adresi','language':'Dil','security':'Güvenlik','credentialNote':'Bu mobil sürümde kamera giriş bilgileri saklanmaz.','version':'Sürüm','check':'Sunucu bağlantısını kontrol et','add':'Kamera ekle','cameraName':'Kamera adı','host':'IP veya ana bilgisayar','brand':'Marka','cancel':'İptal','save':'Kaydet','local':'Yerel demo modu','connecting':'Bağlanıyor…','connected':'Sunucuya bağlı','unavailable':'Sunucu kullanılamıyor • Demo modu','updated':'Kamera listesi güncellendi','failed':'Bağlantı kurulamadı; sunucu adresini ve ağı kontrol edin','saved':'Kamera sunucuya kaydedildi','localOnly':'Yalnızca yerel listeye eklendi; sunucu bağlı değil'}
};
String tr(String lang, String key) => i18n[lang]?[key] ?? i18n['en']![key] ?? key;

class MolidoCctvApp extends StatelessWidget {
  const MolidoCctvApp({super.key, this.homeOverride});
  final Widget? homeOverride;
  @override
  Widget build(BuildContext context) => MaterialApp(
    debugShowCheckedModeBanner: false,
    title: 'DAHUA • Molido CCTV AI',
    theme: ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: ink,
      colorScheme: ColorScheme.fromSeed(seedColor: brandRed, brightness: Brightness.dark),
      useMaterial3: true,
      fontFamily: 'Roboto',
      cardTheme: const CardThemeData(color: panel, elevation: 0),
    ),
    home: homeOverride ?? const AuthGate(),
  );
}

class AuthGate extends StatefulWidget {
  const AuthGate({super.key});
  @override
  State<AuthGate> createState() => _AuthGateState();
}
class _AuthGateState extends State<AuthGate> {
  static const _storage = FlutterSecureStorage();
  final _server = TextEditingController(text: 'http://10.0.2.2:8000');
  final _tenant = TextEditingController();
  final _email = TextEditingController();
  final _password = TextEditingController();
  String _language = 'fa';
  String? _token;
  String _role = 'viewer';
  bool _loading = true;
  String? _error;
  String label(String key) {
    const labels = {
      'fa': {'title':'ورود امن به مرکز نظارت','server':'آدرس سرور','tenant':'شناسه مجموعه','email':'ایمیل','password':'رمز عبور','login':'ورود','note':'توکن ورود فقط در فضای امن اندروید ذخیره می‌شود.','https':'برای اتصال خارج از شبیه‌ساز، HTTPS لازم است.','failed':'ورود انجام نشد؛ اطلاعات و آدرس سرور را بررسی کنید.','language':'زبان'},
      'en': {'title':'Secure sign in','server':'Server URL','tenant':'Tenant slug','email':'Email','password':'Password','login':'Sign in','note':'Your access token is stored in Android secure storage.','https':'HTTPS is required outside the Android emulator.','failed':'Sign-in failed. Check your details and server URL.','language':'Language'},
      'ar': {'title':'تسجيل دخول آمن','server':'عنوان الخادم','tenant':'معرّف المؤسسة','email':'البريد الإلكتروني','password':'كلمة المرور','login':'دخول','note':'يُحفظ رمز الدخول في التخزين الآمن على Android.','https':'يلزم HTTPS خارج محاكي Android.','failed':'فشل الدخول؛ تحقق من البيانات وعنوان الخادم.','language':'اللغة'},
      'tr': {'title':'Güvenli oturum açma','server':'Sunucu URL','tenant':'Kuruluş kodu','email':'E-posta','password':'Parola','login':'Giriş yap','note':'Erişim belirteci Android güvenli depolamasında tutulur.','https':'Android emülatörü dışında HTTPS gerekir.','failed':'Giriş başarısız. Bilgileri ve sunucu adresini kontrol edin.','language':'Dil'},
    };
    return labels[_language]?[key] ?? labels['en']![key]!;
  }
  @override
  void initState() { super.initState(); _restoreSession(); }
  Future<void> _restoreSession() async {
    try {
      final savedServer = await _storage.read(key: 'api_base');
      if (savedServer != null && savedServer.isNotEmpty) _server.text = savedServer;
      final savedToken = await _storage.read(key: 'access_token');
      if (savedToken != null && savedToken.isNotEmpty) {
        final response = await http.get(Uri.parse('${_server.text.trim()}/api/v1/auth/me'),
          headers: {'Authorization': 'Bearer $savedToken'}).timeout(const Duration(seconds: 8));
        if (response.statusCode == 200) {
          final profile = jsonDecode(response.body) as Map<String, dynamic>;
          if (mounted) setState(() { _token = savedToken; _role = profile['role']?.toString() ?? 'viewer'; });
        } else { await _storage.delete(key: 'access_token'); }
      }
    } catch (_) { await _storage.delete(key: 'access_token'); }
    finally { if (mounted) setState(() => _loading = false); }
  }
  Future<void> _signIn() async {
    setState(() { _loading = true; _error = null; });
    try {
      final server = _server.text.trim().replaceAll(RegExp(r'/$'), '');
      final uri = Uri.parse(server);
      if (!{'http', 'https'}.contains(uri.scheme) || uri.host.isEmpty ||
          uri.userInfo.isNotEmpty || uri.query.isNotEmpty || uri.fragment.isNotEmpty ||
          (uri.path.isNotEmpty && uri.path != '/')) throw Exception('Invalid server URL');
      if (uri.scheme == 'http' && !{'10.0.2.2', 'localhost', '127.0.0.1'}.contains(uri.host)) {
        throw Exception('HTTPS required');
      }
      final response = await http.post(Uri.parse('$server/api/v1/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email':_email.text.trim(),'password':_password.text,'tenant_slug':_tenant.text.trim()}))
        .timeout(const Duration(seconds: 12));
      if (response.statusCode != 200) throw Exception('Invalid credentials');
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final token = data['access_token']?.toString();
      if (token == null || token.isEmpty) throw Exception('Missing token');
      final profileResponse = await http.get(Uri.parse('$server/api/v1/auth/me'),
        headers: {'Authorization': 'Bearer $token'}).timeout(const Duration(seconds: 8));
      if (profileResponse.statusCode != 200) throw Exception('Could not load account');
      final profile = jsonDecode(profileResponse.body) as Map<String, dynamic>;
      await _storage.write(key: 'access_token', value: token);
      await _storage.write(key: 'api_base', value: server);
      if (mounted) setState(() { _token = token; _role = profile['role']?.toString() ?? 'viewer'; _server.text = server; });
    } catch (_) { if (mounted) setState(() => _error = label('failed')); }
    finally { if (mounted) setState(() => _loading = false); }
  }
  Future<void> _signOut() async {
    final token = _token;
    final server = _server.text.trim().replaceAll(RegExp(r'/$'), '');
    if (token != null) {
      try { await http.post(Uri.parse('$server/api/v1/auth/logout'),
        headers: {'Authorization':'Bearer $token'}).timeout(const Duration(seconds: 6)); } catch (_) {}
    }
    await _storage.delete(key: 'access_token');
    if (mounted) setState(() => _token = null);
  }
  @override
  void dispose() { _server.dispose(); _tenant.dispose(); _email.dispose(); _password.dispose(); super.dispose(); }
  @override
  Widget build(BuildContext context) {
    if (_loading) return const Scaffold(backgroundColor: ink, body: Center(child:CircularProgressIndicator()));
    if (_token != null) return DashboardPage(token:_token!, role:_role, initialApiBase:_server.text, onLogout:_signOut);
    final rtl = _language == 'fa' || _language == 'ar';
    return Directionality(textDirection:rtl?TextDirection.rtl:TextDirection.ltr, child:Scaffold(
      backgroundColor:ink, body:SafeArea(child:Center(child:SingleChildScrollView(
        padding:const EdgeInsets.all(22), child:ConstrainedBox(constraints:const BoxConstraints(maxWidth:440),
          child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
            Container(width:62,height:62,alignment:Alignment.center,decoration:BoxDecoration(color:brandRed,borderRadius:BorderRadius.circular(18)),
              child:const Icon(Icons.videocam_rounded,size:34,color:Colors.white)),
            const SizedBox(height:22),
            const Text('MOLIDO CCTV AI',textAlign:TextAlign.center,style:TextStyle(fontSize:22,fontWeight:FontWeight.w900,letterSpacing:1.2)),
            const SizedBox(height:8),Text(label('title'),textAlign:TextAlign.center,style:const TextStyle(fontSize:17,color:Colors.white70)),
            const SizedBox(height:24),
            DropdownButtonFormField<String>(initialValue:_language,decoration:InputDecoration(labelText:label('language')),
              items:const [DropdownMenuItem(value:'fa',child:Text('فارسی')),DropdownMenuItem(value:'en',child:Text('English')),DropdownMenuItem(value:'ar',child:Text('العربية')),DropdownMenuItem(value:'tr',child:Text('Türkçe'))],
              onChanged:(v){if(v!=null)setState(()=>_language=v);}),
            const SizedBox(height:12),TextField(controller:_server,keyboardType:TextInputType.url,decoration:InputDecoration(labelText:label('server'),prefixIcon:const Icon(Icons.dns_outlined))),
            const SizedBox(height:12),TextField(controller:_tenant,decoration:InputDecoration(labelText:label('tenant'),prefixIcon:const Icon(Icons.apartment))),
            const SizedBox(height:12),TextField(controller:_email,keyboardType:TextInputType.emailAddress,decoration:InputDecoration(labelText:label('email'),prefixIcon:const Icon(Icons.email_outlined))),
            const SizedBox(height:12),TextField(controller:_password,obscureText:true,decoration:InputDecoration(labelText:label('password'),prefixIcon:const Icon(Icons.lock_outline)),onSubmitted:(_)=>_signIn()),
            if(_error!=null) ...[const SizedBox(height:12),Text(_error!,style:const TextStyle(color:Colors.redAccent))],
            const SizedBox(height:18),FilledButton(style:FilledButton.styleFrom(backgroundColor:brandRed,padding:const EdgeInsets.symmetric(vertical:15)),
              onPressed:_loading?null:_signIn,child:Text(label('login'),style:const TextStyle(fontWeight:FontWeight.bold))),
            const SizedBox(height:14),Text(label('note'),textAlign:TextAlign.center,style:const TextStyle(color:Colors.white54,fontSize:11)),
            Text(label('https'),textAlign:TextAlign.center,style:const TextStyle(color:Colors.white38,fontSize:10)),
          ]),
        ),
      ))),
    ));
  }
}

class CameraItem {
  CameraItem({required this.name, required this.brand, required this.host, required this.status, this.location = 'Not set'});
  final String name, brand, host, status, location;
  factory CameraItem.fromJson(Map<String, dynamic> j) => CameraItem(
    name: j['name'] ?? 'Camera', brand: j['brand'] ?? 'Generic',
    host: j['host'] ?? '', status: j['status'] ?? 'pending',
    location: j['location'] ?? 'Not set',
  );
}

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key, required this.token, required this.role, required this.initialApiBase, required this.onLogout});
  final String token;
  final String role;
  final String initialApiBase;
  final Future<void> Function() onLogout;
  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  late String apiBase;
  Map<String, String> get authHeaders => {'Authorization': 'Bearer ${widget.token}'};
  @override
  void initState() {
    super.initState();
    apiBase = widget.initialApiBase;
  }
  bool connecting = false;
  String connection = 'Local demo mode';
  int selectedTab = 0;
  String language = 'fa';
  String t(String key) => tr(language, key);
  TextDirection get pageDirection => language == 'fa' || language == 'ar' ? TextDirection.rtl : TextDirection.ltr;
  final recorders = <Map<String,dynamic>>[];
  final cameras = <CameraItem>[
    CameraItem(name: 'ورودی اصلی', brand: 'Dahua', host: '192.168.1.101', status: 'demo'),
    CameraItem(name: 'پارکینگ', brand: 'Dahua', host: '192.168.1.102', status: 'demo'),
    CameraItem(name: 'انبار', brand: 'ONVIF', host: '192.168.1.103', status: 'demo'),
  ];


  Future<void> createUser() async {
    final email = TextEditingController();
    final password = TextEditingController();
    String role = 'employee';
    final ok = await showDialog<bool>(context: context, builder: (ctx) => StatefulBuilder(
      builder: (ctx, refresh) => AlertDialog(
        backgroundColor: panel,
        title: Text(language == 'fa' ? 'ایجاد حساب کاربری' : language == 'ar' ? 'إنشاء حساب' : language == 'tr' ? 'Hesap oluştur' : 'Create account'),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          TextField(controller: email, keyboardType: TextInputType.emailAddress,
            decoration: InputDecoration(labelText: language == 'fa' ? 'ایمیل' : 'Email')),
          TextField(controller: password, obscureText: true,
            decoration: InputDecoration(labelText: language == 'fa' ? 'رمز عبور (حداقل ۱۲ کاراکتر)' : 'Password (min 12 characters)')),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            initialValue: role,
            decoration: InputDecoration(labelText: language == 'fa' ? 'نقش کاربر' : 'Account role'),
            items: [
              DropdownMenuItem(value: 'manager', child: Text(language == 'fa' ? 'مدیر' : 'Manager')),
              DropdownMenuItem(value: 'employee', child: Text(language == 'fa' ? 'کارمند' : 'Employee')),
              DropdownMenuItem(value: 'viewer', child: Text(language == 'fa' ? 'مشاهده‌گر' : 'Viewer')),
            ],
            onChanged: (value) { if (value != null) refresh(() => role = value); },
          ),
        ]),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(t('cancel'))),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: Text(t('save'))),
        ],
      ),
    ));
    if (ok == true) {
      try {
        final response = await http.post(Uri.parse('$apiBase/api/v1/auth/users'),
          headers: {...authHeaders, 'Content-Type': 'application/json'},
          body: jsonEncode({'email': email.text.trim(), 'password': password.text, 'role': role}))
          .timeout(const Duration(seconds: 12));
        if (response.statusCode != 201) throw Exception('HTTP ${response.statusCode}');
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(
          language == 'fa' ? 'حساب کاربری با موفقیت ایجاد شد' : 'Account created successfully')));
      } catch (_) {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(
          language == 'fa' ? 'ایجاد حساب انجام نشد؛ مجوز مدیر و اطلاعات را بررسی کنید' : 'Could not create account; check manager access and fields')));
      }
    }
    email.dispose(); password.dispose();
  }

  Future<void> syncRecorders() async {
    try {
      final res = await http.get(Uri.parse('$apiBase/api/v1/recorders'), headers: authHeaders).timeout(const Duration(seconds: 8));
      if (res.statusCode != 200) throw Exception('HTTP ${res.statusCode}');
      final data = (jsonDecode(res.body) as List).cast<Map<String,dynamic>>();
      if (mounted) setState(() { recorders..clear()..addAll(data); });
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content:Text(language=='fa'?'دریافت فهرست دستگاه‌های ضبط ناموفق بود':'Could not load recorder list')));
    }
  }

  Future<void> testRecorder(Map<String,dynamic> recorder) async {
    final username = TextEditingController();
    final password = TextEditingController();
    final ok = await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(
      backgroundColor:panel,
      title:Text(language=='fa'?'آزمون اتصال دستگاه':'Test recorder connection'),
      content:Column(mainAxisSize:MainAxisSize.min,children:[
        TextField(controller:username,decoration:InputDecoration(labelText:language=='fa'?'نام کاربری مدیر':'Recorder admin username')),
        TextField(controller:password,obscureText:true,decoration:InputDecoration(labelText:language=='fa'?'رمز مدیر دستگاه':'Recorder admin password')),
      ]),
      actions:[
        TextButton(onPressed:()=>Navigator.pop(ctx,false),child:Text(language=='fa'?'انصراف':'Cancel')),
        FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:Text(language=='fa'?'آزمایش':'Test')),
      ],
    ));
    if(ok==true) {
      try {
        final recorderId = recorder['id'].toString();
        if(recorder['connection_method']=='dahua_p2p') {
          if(Uri.parse(apiBase).scheme!='https') throw Exception('P2P credentials require HTTPS');
          final state=await http.post(Uri.parse('$apiBase/api/v1/recorders/$recorderId/p2p-connect-test'),
            headers:{...authHeaders,'Content-Type':'application/json'},
            body:jsonEncode({'username':username.text.trim(),'password':password.text})).timeout(const Duration(seconds:8));
          if(state.statusCode==501) {
            if(mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(
              language=='fa'?'اتصال ابری هنوز فعال نیست؛ SDK/API رسمی مجاز داهوا تنظیم نشده است':'Cloud connection is not enabled; authorized Dahua SDK/API is not configured')));
          } else if(state.statusCode!=200) {
            throw Exception('P2P connection test failed');
          }
          await syncRecorders();
          username.dispose();password.dispose();
          return;
        }
        final response=await http.post(Uri.parse('$apiBase/api/v1/recorders/$recorderId/connect-test'),
          headers:{...authHeaders,'Content-Type':'application/json'},
          body:jsonEncode({'username':username.text,'password':password.text})).timeout(const Duration(seconds:20));
        if(response.statusCode!=200) throw Exception('HTTP ${response.statusCode}');
        final result=jsonDecode(response.body) as Map<String,dynamic>;
        final count=result['channel_count']??0;
        if(mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(
          language=='fa'?'اتصال: موفق • کانال‌های شناسایی‌شده: $count':'Connected • Discovered channels: $count')));
        await syncRecorders();
      } catch (_) {
        if(mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(
          language=='fa'?'اتصال برقرار نشد؛ IP، پورت، دسترسی ONVIF و رمز را بررسی کنید':'Connection failed; check IP, port, ONVIF access and credentials')));
      }
    }
    username.dispose();password.dispose();
  }

  Future<void> syncCameras() async {
    setState(() { connecting = true; connection = t('connecting'); });
    try {
      final res = await http.get(Uri.parse('$apiBase/api/v1/cameras'), headers: authHeaders).timeout(const Duration(seconds: 6));
      if (res.statusCode != 200) throw Exception('HTTP ${res.statusCode}');
      final data = (jsonDecode(res.body) as List).map((e) => CameraItem.fromJson(e as Map<String, dynamic>)).toList();
      if (!mounted) return;
      setState(() { cameras..clear()..addAll(data); connection = t('connected'); });
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(t('updated'))));
    } catch (_) {
      if (!mounted) return;
      setState(() => connection = t('unavailable'));
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(t('failed'))));
    } finally { if (mounted) setState(() => connecting = false); }
  }

  Future<void> addCamera() async {
    final name = TextEditingController();
    final host = TextEditingController();
    final brand = TextEditingController(text: 'Dahua');
    final ok = await showDialog<bool>(context: context, builder: (ctx) => AlertDialog(
      backgroundColor: panel, title: Text(t('add')),
      content: Column(mainAxisSize: MainAxisSize.min, children: [
        TextField(controller: name, decoration: InputDecoration(labelText: t('cameraName'))),
        TextField(controller: host, decoration: InputDecoration(labelText: t('host'), hintText: '192.168.1.100')),
        TextField(controller: brand, decoration: InputDecoration(labelText: t('brand'))),
      ]),
      actions: [TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(t('cancel'))), FilledButton(onPressed: () => Navigator.pop(ctx, true), child: Text(t('save')))],
    ));
    if (ok != true || name.text.trim().isEmpty || host.text.trim().isEmpty) return;
    try {
      final res = await http.post(Uri.parse('$apiBase/api/v1/cameras'),
        headers: {...authHeaders,'Content-Type':'application/json'},
        body: jsonEncode({'name':name.text.trim(),'brand':brand.text.trim(),'protocol':'onvif','host':host.text.trim()})).timeout(const Duration(seconds: 6));
      if (res.statusCode != 201) throw Exception('HTTP ${res.statusCode}');
      setState(() => cameras.add(CameraItem.fromJson(jsonDecode(res.body))));
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(t('saved'))));
    } catch (_) {
      setState(() => cameras.add(CameraItem(name:name.text.trim(),brand:brand.text.trim(),host:host.text.trim(),status:'local')));
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(t('localOnly'))));
    } finally { name.dispose(); host.dispose(); brand.dispose(); }
  }


  Future<void> addRecorder() async {
    final name = TextEditingController(), brand = TextEditingController(text: 'Dahua');
    final model = TextEditingController(), host = TextEditingController(), port = TextEditingController(text: '37777');
    final serial = TextEditingController(), username = TextEditingController(), password = TextEditingController();
    String method = 'ip', type = 'dvr';
    String label(String key) {
      const labels = {
        'fa': {'add':'افزودن دستگاه ضبط','name':'نام دستگاه','brand':'برند','model':'مدل (اختیاری)','type':'نوع دستگاه','method':'روش اتصال','ip':'اتصال با IP','p2p':'P2P سازگار با DMSS داهوا','host':'IP یا Host','port':'پورت','serialNo':'شماره سریال / Device ID','user':'نام کاربری مدیر','pass':'رمز مدیر DVR/NVR','save':'ثبت دستگاه','cancel':'انصراف','failed':'ثبت دستگاه انجام نشد؛ اطلاعات و اتصال سرور را بررسی کنید','saved':'دستگاه ضبط ثبت شد؛ اتصال واقعی پس از افزودن آداپتور سازنده فعال می‌شود'},
        'en': {'add':'Add recorder','name':'Device name','brand':'Brand','model':'Model (optional)','type':'Device type','method':'Connection method','ip':'Connect by IP','p2p':'Dahua DMSS-compatible P2P','host':'IP or Host','port':'Port','serialNo':'Serial number / Device ID','user':'Recorder admin username','pass':'Recorder admin password','save':'Register device','cancel':'Cancel','failed':'Could not register device; check fields and server','saved':'Recorder registered; live connection requires the vendor adapter'},
        'ar': {'add':'إضافة جهاز تسجيل','name':'اسم الجهاز','brand':'العلامة التجارية','model':'الطراز (اختياري)','type':'نوع الجهاز','method':'طريقة الاتصال','ip':'الاتصال عبر IP','p2p':'P2P متوافق مع DMSS من Dahua','host':'IP أو المضيف','port':'المنفذ','serialNo':'الرقم التسلسلي / Device ID','user':'اسم مستخدم المدير','pass':'كلمة مرور مدير جهاز DVR/NVR','save':'تسجيل الجهاز','cancel':'إلغاء','failed':'تعذر تسجيل الجهاز؛ تحقق من البيانات والخادم','saved':'تم تسجيل الجهاز؛ الاتصال الفعلي يتطلب محول الشركة'},
        'tr': {'add':'Kayıt cihazı ekle','name':'Cihaz adı','brand':'Marka','model':'Model (isteğe bağlı)','type':'Cihaz türü','method':'Bağlantı yöntemi','ip':'IP ile bağlan','p2p':'Dahua DMSS uyumlu P2P','host':'IP veya ana bilgisayar','port':'Bağlantı noktası','serialNo':'Seri numarası / Device ID','user':'Yönetici kullanıcı adı','pass':'DVR/NVR yönetici şifresi','save':'Cihazı kaydet','cancel':'İptal','failed':'Cihaz kaydedilemedi; alanları ve sunucuyu kontrol edin','saved':'Kayıt cihazı eklendi; gerçek bağlantı üretici adaptörü gerektirir'}
      };
      return labels[language]?[key] ?? labels['en']![key]!;
    }
    final ok = await showDialog<bool>(context: context, builder: (ctx) => StatefulBuilder(
      builder: (ctx, refresh) => AlertDialog(
        backgroundColor: panel, title: Text(label('add')),
        content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
          TextField(controller:name,decoration:InputDecoration(labelText:label('name'))),
          TextField(controller:brand,decoration:InputDecoration(labelText:label('brand'))),
          TextField(controller:model,decoration:InputDecoration(labelText:label('model'))),
          DropdownButtonFormField<String>(initialValue:type,decoration:InputDecoration(labelText:label('type')),
            items:const [DropdownMenuItem(value:'dvr',child:Text('DVR')),DropdownMenuItem(value:'nvr',child:Text('NVR')),DropdownMenuItem(value:'xvr',child:Text('XVR'))],
            onChanged:(v){if(v!=null)refresh(()=>type=v);}),
          DropdownButtonFormField<String>(initialValue:method,decoration:InputDecoration(labelText:label('method')),
            items:[DropdownMenuItem(value:'ip',child:Text(label('ip'))),DropdownMenuItem(value:'dahua_p2p',child:Text(label('p2p')))],
            onChanged:(v){if(v!=null)refresh(()=>method=v);}),
          if(method=='ip') ...[
            TextField(controller:host,decoration:InputDecoration(labelText:label('host'))),
            TextField(controller:port,keyboardType:TextInputType.number,decoration:InputDecoration(labelText:label('port'))),
            TextField(controller:username,decoration:InputDecoration(labelText:label('user'))),
            TextField(controller:password,obscureText:true,decoration:InputDecoration(labelText:label('pass'))),
          ] else if(method=='dahua_p2p') ...[
            TextField(controller:serial,decoration:InputDecoration(labelText:label('serialNo'))),
            TextField(controller:username,decoration:InputDecoration(labelText:label('user'))),
            TextField(controller:password,obscureText:true,decoration:InputDecoration(labelText:label('pass'))),
            Padding(padding:const EdgeInsets.only(top:8),child:Text(language=='fa'?'فقط شماره سریال، نام کاربری مدیر و رمز مدیر خود DVR/NVR وارد شود. P2P باید روی دستگاه فعال و Online باشد. رمز حساب DMSS قابل استفاده نیست. اتصال ابری Molido هنوز به SDK/API مجاز داهوا نیاز دارد.':'Enter the recorder serial number, recorder admin username and recorder admin password. P2P must be enabled and Online. Do not use the DMSS account password. Molido cloud transport still requires an authorized Dahua SDK/API.',style:const TextStyle(fontSize:11,color:Colors.white60))),
          ],
        ])),
        actions:[
          TextButton(onPressed:()=>Navigator.pop(ctx,false),child:Text(label('cancel'))),
          FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:Text(label('save'))),
        ],
      ),
    ));
    if (ok == true) {
      try {
        final payload = <String,dynamic>{
          'name':name.text.trim(),'brand':brand.text.trim(),'model':model.text.trim().isEmpty?null:model.text.trim(),
          'recorder_type':type,'connection_method':method,
          'host':method=='ip'?host.text.trim():null,
          'port':method=='ip'?int.tryParse(port.text.trim()):null,
          'serial_number':method!='ip'?serial.text.trim():null,
          'username':method=='ip'?(username.text.trim().isEmpty?null:username.text.trim()):null,
          'password':method=='ip'?password.text:null,
        };
        if(method=='dahua_p2p' && Uri.parse(apiBase).scheme!='https') {
          throw Exception('P2P credentials require HTTPS');
        }
        final response = await http.post(Uri.parse('$apiBase/api/v1/recorders'),
          headers:{...authHeaders,'Content-Type':'application/json'},body:jsonEncode(payload)).timeout(const Duration(seconds:8));
        if (response.statusCode != 201) throw Exception('HTTP ${response.statusCode}');
        final created = jsonDecode(response.body) as Map<String,dynamic>;
        final createdId = created['id'].toString();
        if(method=='ip') {
          final tested=await http.post(Uri.parse('$apiBase/api/v1/recorders/$createdId/connect-test'),
            headers:{...authHeaders,'Content-Type':'application/json'},
            body:jsonEncode({'username':username.text.trim(),'password':password.text})).timeout(const Duration(seconds:20));
          if(tested.statusCode==200) {
            final result=jsonDecode(tested.body) as Map<String,dynamic>;
            final count=result['channel_count']??0;
            if(mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(
              language=='fa'?'دستگاه ثبت شد؛ کانال شناسایی‌شده: $count':'Recorder saved; channels discovered: $count')));
          } else {
            if(mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(
              language=='fa'?'دستگاه ثبت شد اما اتصال برقرار نشد':'Recorder saved, but connection test failed')));
          }
        } else if(method=='dahua_p2p') {
          final state=await http.get(Uri.parse('$apiBase/api/v1/recorders/$createdId/p2p-status'), headers: authHeaders).timeout(const Duration(seconds:8));
          if(state.statusCode!=200) throw Exception('P2P status unavailable');
          if(mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(
            language=='fa'?'سریال ثبت شد؛ رمز دستگاه ذخیره نشد. اتصال Molido تا دریافت SDK/API مجاز فعال نیست.':'Serial saved; device credentials were not stored. Molido cloud access awaits an authorized SDK/API.')));
        } else {
          if(mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(
            language=='fa'?'سریال ثبت شد؛ آداپتور P2P سازنده هنوز نیازمند SDK است':'Serial saved; manufacturer P2P SDK adapter is still required')));
        }
        await syncRecorders();
      } catch (_) {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(label('failed'))));
      }
    }
    name.dispose();brand.dispose();model.dispose();host.dispose();port.dispose();
    serial.dispose();username.dispose();password.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final pages = [_home(), _cameraList(), _events(), _settings()];
    return Directionality(textDirection: pageDirection, child: Scaffold(
      appBar: AppBar(
        backgroundColor: ink,
        title: Row(children: [
          Container(width:34,height:34,decoration:BoxDecoration(color:brandRed,borderRadius:BorderRadius.circular(10)),child:const Icon(Icons.videocam_rounded,color:Colors.white)),
          const SizedBox(width:10),
          const Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
            Text('MOLIDO CCTV AI',style:TextStyle(fontSize:15,fontWeight:FontWeight.w900,letterSpacing:1)),
            Text('DAHUA • MULTI-BRAND',style:TextStyle(fontSize:9,color:Colors.white54,letterSpacing:1.2)),
          ]),
        ]),
        actions:[IconButton(onPressed:syncCameras,icon:const Icon(Icons.sync_rounded),tooltip:t('sync'))],
      ),
      body: pages[selectedTab],
      floatingActionButton: selectedTab == 1 ? FloatingActionButton(
        onPressed:addCamera, backgroundColor:brandRed, child:const Icon(Icons.add)
      ) : null,
      bottomNavigationBar: NavigationBar(
        backgroundColor:panel, indicatorColor:brandRed.withValues(alpha:.2),
        selectedIndex:selectedTab, onDestinationSelected:(i)=>setState(()=>selectedTab=i),
        destinations:[
          NavigationDestination(icon:Icon(Icons.dashboard_outlined),selectedIcon:Icon(Icons.dashboard),label:t('home')),
          NavigationDestination(icon:Icon(Icons.cameraswitch_outlined),selectedIcon:Icon(Icons.cameraswitch),label:t('cameras')),
          NavigationDestination(icon:Icon(Icons.notifications_active_outlined),selectedIcon:Icon(Icons.notifications_active),label:t('events')),
          NavigationDestination(icon:Icon(Icons.settings_outlined),selectedIcon:Icon(Icons.settings),label:t('settings')),
        ],
      ),
    ));
  }

  Widget _home() => ListView(padding:const EdgeInsets.all(16),children:[
    Container(padding:const EdgeInsets.all(18),decoration:BoxDecoration(
      gradient:const LinearGradient(colors:[Color(0xFF292D35),Color(0xFF171A20)]),
      borderRadius:BorderRadius.circular(20),border:Border.all(color:Colors.white10)),
      child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
        Row(children:[Expanded(child:Text(t('center'),style:TextStyle(fontSize:20,fontWeight:FontWeight.bold))),_statusDot()]),
        const SizedBox(height:6),Text(connection,style:const TextStyle(color:Colors.white60,fontSize:12)),
        const SizedBox(height:18),Row(children:[
          _metric(t('total'),'${cameras.length}',Icons.videocam_outlined),
          const SizedBox(width:12),_metric(t('online'),'—',Icons.wifi_rounded),
          const SizedBox(width:12),_metric(t('alerts'),'۰',Icons.notifications_none),
        ]),
      ]),
    ),
    const SizedBox(height:20),
    Row(mainAxisAlignment:MainAxisAlignment.spaceBetween,children:[
      Text(t('live'),style:TextStyle(fontSize:17,fontWeight:FontWeight.bold)),
      TextButton(onPressed:()=>setState(()=>selectedTab=1),child:Text(t('all'))),
    ]),
    GridView.builder(shrinkWrap:true,physics:const NeverScrollableScrollPhysics(),itemCount:cameras.take(4).length,
      gridDelegate:const SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount:2,childAspectRatio:1.18,crossAxisSpacing:10,mainAxisSpacing:10),
      itemBuilder:(context,i)=>_previewCard(cameras[i])),
    const SizedBox(height:16),
    Container(padding:const EdgeInsets.all(14),decoration:BoxDecoration(color:panel,borderRadius:BorderRadius.circular(16)),
      child:Row(children:[Icon(Icons.info_outline,color:brandRed),SizedBox(width:10),Expanded(child:Text(t('demo'),style:TextStyle(fontSize:12,color:Colors.white70)))])),
  ]);

  Widget _metric(String label,String value,IconData icon)=>Expanded(child:Container(padding:const EdgeInsets.all(10),decoration:BoxDecoration(color:Colors.white.withValues(alpha:.05),borderRadius:BorderRadius.circular(14)),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Icon(icon,color:brandRed,size:19),const SizedBox(height:8),Text(value,style:const TextStyle(fontSize:21,fontWeight:FontWeight.bold)),Text(label,style:const TextStyle(fontSize:10,color:Colors.white60))])));
  Widget _statusDot()=>Row(children:[Container(width:8,height:8,decoration:const BoxDecoration(color:Color(0xFFFFB74D),shape:BoxShape.circle)),const SizedBox(width:6),const Text('TEST',style:TextStyle(color:Color(0xFFFFB74D),fontSize:10,fontWeight:FontWeight.bold))]);
  Widget _previewCard(CameraItem c)=>Container(decoration:BoxDecoration(color:panel,borderRadius:BorderRadius.circular(16),border:Border.all(color:Colors.white10)),clipBehavior:Clip.antiAlias,child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
    Expanded(child:Container(color:const Color(0xFF252A32),child:const Center(child:Icon(Icons.videocam_off_outlined,size:34,color:Colors.white24)))),
    Padding(padding:const EdgeInsets.all(9),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(c.name,style:const TextStyle(fontWeight:FontWeight.bold,fontSize:12),maxLines:1,overflow:TextOverflow.ellipsis),Text('${c.brand} • ${c.host}',style:const TextStyle(color:Colors.white54,fontSize:9),maxLines:1,overflow:TextOverflow.ellipsis)])),
  ]));

  Widget _cameraList()=>ListView(padding:const EdgeInsets.all(16),children:[
    Row(mainAxisAlignment:MainAxisAlignment.spaceBetween,children:[Text(t('manage'),style:TextStyle(fontSize:19,fontWeight:FontWeight.bold)),Text('${cameras.length} ${t('device')}',style:const TextStyle(color:Colors.white54))]),
    const SizedBox(height:12),
    const SizedBox(height:12),
    Row(mainAxisAlignment:MainAxisAlignment.spaceBetween,children:[
      Text(language=='fa'?'دستگاه‌های ضبط':'Recorders',style:TextStyle(fontSize:17,fontWeight:FontWeight.bold)),
      TextButton(onPressed:syncRecorders,child:Text(language=='fa'?'بروزرسانی':'Refresh')),
    ]),
    ...recorders.map((r) {
      final recorderName = r['name']?.toString() ?? '';
      final recorderType = r['recorder_type']?.toString().toUpperCase() ?? '';
      final recorderBrand = r['brand']?.toString() ?? '';
      final connectionMethod = r['connection_method']?.toString() ?? '';
      final recorderStatus = r['status']?.toString() ?? '';
      final recorderAddress = (r['host'] ?? r['serial_number'] ?? '').toString();
      return Card(child:ListTile(
        leading:const Icon(Icons.dvr,color:brandRed),
        title:Text('$recorderName • $recorderType'),
        subtitle:Text('$recorderBrand • $connectionMethod • $recorderStatus\n$recorderAddress',style:const TextStyle(fontSize:11)),
        isThreeLine:true,
        trailing:IconButton(icon:const Icon(Icons.wifi_tethering),tooltip:language=='fa'?'تست اتصال':'Test connection',
          onPressed:()=>testRecorder(r)),
      ));
    }),
    ...cameras.map((c)=>Card(child:ListTile(leading:Container(width:42,height:42,decoration:BoxDecoration(color:brandRed.withValues(alpha:.13),borderRadius:BorderRadius.circular(12)),child:const Icon(Icons.videocam,color:brandRed)),title:Text(c.name),subtitle:Text('${c.brand}  •  ${c.host}\n${c.location}',style:const TextStyle(fontSize:11)),isThreeLine:true,trailing:const Icon(Icons.chevron_left)))),
    const SizedBox(height:12),FilledButton.icon(style:FilledButton.styleFrom(backgroundColor:brandRed),onPressed:addRecorder,icon:const Icon(Icons.dvr),label:Text(language=='fa'?'افزودن DVR / NVR':language=='ar'?'إضافة DVR / NVR':language=='tr'?'DVR / NVR ekle':'Add DVR / NVR')),
    const SizedBox(height:8),OutlinedButton.icon(onPressed:connecting?null:(){syncCameras();syncRecorders();},icon:const Icon(Icons.sync),label:Text(connecting?t('syncing'):t('syncServer'))),
  ]);

  Widget _events()=>ListView(padding:const EdgeInsets.all(16),children:[
    Text(t('eventTitle'),style:TextStyle(fontSize:19,fontWeight:FontWeight.bold)),const SizedBox(height:18),
    Container(padding:const EdgeInsets.all(16),decoration:BoxDecoration(color:panel,borderRadius:BorderRadius.circular(16)),child:Column(children:[Icon(Icons.notifications_none,size:42,color:Colors.white38),SizedBox(height:10),Text(t('empty'),style:TextStyle(color:Colors.white70)),SizedBox(height:5),Text(t('emptyHelp'),textAlign:TextAlign.center,style:TextStyle(color:Colors.white38,fontSize:12))])),
  ]);

  Widget _settings()=>ListView(padding:const EdgeInsets.all(16),children:[
    Text(t('appSettings'),style:TextStyle(fontSize:19,fontWeight:FontWeight.bold)),const SizedBox(height:12),
    Card(child:ListTile(leading:const Icon(Icons.dns_outlined,color:brandRed),title:Text(t('server')),subtitle:Text(apiBase))),
    Card(child:ListTile(leading:const Icon(Icons.language,color:brandRed),title:Text(t('language')),trailing:DropdownButton<String>(value:language,items:const [DropdownMenuItem(value:'fa',child:Text('فارسی')),DropdownMenuItem(value:'en',child:Text('English')),DropdownMenuItem(value:'ar',child:Text('العربية')),DropdownMenuItem(value:'tr',child:Text('Türkçe'))],onChanged:(v){if(v!=null)setState(()=>language=v);}))),
    Card(child:ListTile(leading:const Icon(Icons.security,color:brandRed),title:Text(t('security')),subtitle:Text(t('credentialNote')))),
    Card(child:ListTile(leading:const Icon(Icons.info_outline,color:brandRed),title:Text(t('version')),subtitle:const Text('0.1.0 • Android Test'))),
    const SizedBox(height:10),FilledButton.icon(style:FilledButton.styleFrom(backgroundColor:brandRed),onPressed:syncCameras,icon:const Icon(Icons.link),label:Text(t('check'))),
    if(widget.role == 'manager') ...[
      const SizedBox(height:10),OutlinedButton.icon(onPressed:createUser,icon:const Icon(Icons.person_add_alt_1),label:Text(language=='fa'?'ایجاد حساب مدیر / کارمند / مشاهده‌گر':'Create manager / employee / viewer account')),
    ],
    const SizedBox(height:10),OutlinedButton.icon(onPressed:(){widget.onLogout();},icon:const Icon(Icons.logout),label:Text(language=='fa'?'خروج امن':language=='ar'?'تسجيل الخروج':language=='tr'?'Çıkış yap':'Sign out')),
  ]);
}
