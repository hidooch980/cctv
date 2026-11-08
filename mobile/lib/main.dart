import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() => runApp(const MolidoCctvApp());

const brandRed = Color(0xFFE3262E);
const ink = Color(0xFF101216);
const panel = Color(0xFF1B1F25);

class MolidoCctvApp extends StatelessWidget {
  const MolidoCctvApp({super.key});
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
    home: const DashboardPage(),
  );
}

class CameraItem {
  CameraItem({required this.name, required this.brand, required this.host, required this.status, this.location = 'محل نصب ثبت نشده'});
  final String name, brand, host, status, location;
  factory CameraItem.fromJson(Map<String, dynamic> j) => CameraItem(
    name: j['name'] ?? 'Camera', brand: j['brand'] ?? 'Generic',
    host: j['host'] ?? '', status: j['status'] ?? 'pending',
    location: j['location'] ?? 'بدون موقعیت',
  );
}

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});
  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  String apiBase = 'http://10.0.2.2:8000';
  bool connecting = false;
  String connection = 'حالت آزمایشی محلی';
  int selectedTab = 0;
  final cameras = <CameraItem>[
    CameraItem(name: 'ورودی اصلی', brand: 'Dahua', host: '192.168.1.101', status: 'demo'),
    CameraItem(name: 'پارکینگ', brand: 'Dahua', host: '192.168.1.102', status: 'demo'),
    CameraItem(name: 'انبار', brand: 'ONVIF', host: '192.168.1.103', status: 'demo'),
  ];

  Future<void> syncCameras() async {
    setState(() { connecting = true; connection = 'در حال اتصال…'; });
    try {
      final res = await http.get(Uri.parse('$apiBase/api/v1/cameras')).timeout(const Duration(seconds: 6));
      if (res.statusCode != 200) throw Exception('HTTP ${res.statusCode}');
      final data = (jsonDecode(res.body) as List).map((e) => CameraItem.fromJson(e as Map<String, dynamic>)).toList();
      if (!mounted) return;
      setState(() { cameras..clear()..addAll(data); connection = 'متصل به سرور'; });
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('فهرست دوربین‌ها به‌روزرسانی شد')));
    } catch (_) {
      if (!mounted) return;
      setState(() => connection = 'سرور در دسترس نیست • حالت آزمایشی');
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('اتصال برقرار نشد؛ آدرس سرور و شبکه را بررسی کنید')));
    } finally { if (mounted) setState(() => connecting = false); }
  }

  Future<void> addCamera() async {
    final name = TextEditingController();
    final host = TextEditingController();
    final brand = TextEditingController(text: 'Dahua');
    final ok = await showDialog<bool>(context: context, builder: (ctx) => AlertDialog(
      backgroundColor: panel, title: const Text('افزودن دوربین'),
      content: Column(mainAxisSize: MainAxisSize.min, children: [
        TextField(controller: name, decoration: const InputDecoration(labelText: 'نام دوربین')),
        TextField(controller: host, decoration: const InputDecoration(labelText: 'IP یا Host', hintText: '192.168.1.100')),
        TextField(controller: brand, decoration: const InputDecoration(labelText: 'برند')),
      ]),
      actions: [TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('انصراف')), FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('ثبت'))],
    ));
    if (ok != true || name.text.trim().isEmpty || host.text.trim().isEmpty) return;
    try {
      final res = await http.post(Uri.parse('$apiBase/api/v1/cameras'),
        headers: {'Content-Type':'application/json'},
        body: jsonEncode({'name':name.text.trim(),'brand':brand.text.trim(),'protocol':'onvif','host':host.text.trim()})).timeout(const Duration(seconds: 6));
      if (res.statusCode != 201) throw Exception('HTTP ${res.statusCode}');
      setState(() => cameras.add(CameraItem.fromJson(jsonDecode(res.body))));
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('دوربین در سرور ثبت شد')));
    } catch (_) {
      setState(() => cameras.add(CameraItem(name:name.text.trim(),brand:brand.text.trim(),host:host.text.trim(),status:'local')));
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('فقط در فهرست محلی افزوده شد؛ سرور متصل نیست')));
    } finally { name.dispose(); host.dispose(); brand.dispose(); }
  }

  Future<void> editServer() async {
    final field = TextEditingController(text: apiBase);
    final ok = await showDialog<bool>(context: context, builder: (ctx) => AlertDialog(
      backgroundColor: panel, title: const Text('نشانی سرور'),
      content: TextField(controller: field, keyboardType: TextInputType.url, decoration: const InputDecoration(hintText:'http://192.168.1.10:8000')),
      actions: [TextButton(onPressed:()=>Navigator.pop(ctx,false), child:const Text('انصراف')), FilledButton(onPressed:()=>Navigator.pop(ctx,true), child:const Text('ذخیره'))],
    ));
    if (ok == true && field.text.trim().isNotEmpty) setState(() => apiBase = field.text.trim().replaceAll(RegExp(r'/$'), ''));
    field.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final pages = [_home(), _cameraList(), _events(), _settings()];
    return Directionality(textDirection: TextDirection.rtl, child: Scaffold(
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
        actions:[IconButton(onPressed:syncCameras,icon:const Icon(Icons.sync_rounded),tooltip:'همگام‌سازی')],
      ),
      body: pages[selectedTab],
      floatingActionButton: selectedTab == 1 ? FloatingActionButton(
        onPressed:addCamera, backgroundColor:brandRed, child:const Icon(Icons.add)
      ) : null,
      bottomNavigationBar: NavigationBar(
        backgroundColor:panel, indicatorColor:brandRed.withOpacity(.2),
        selectedIndex:selectedTab, onDestinationSelected:(i)=>setState(()=>selectedTab=i),
        destinations:const [
          NavigationDestination(icon:Icon(Icons.dashboard_outlined),selectedIcon:Icon(Icons.dashboard),label:'خانه'),
          NavigationDestination(icon:Icon(Icons.cameraswitch_outlined),selectedIcon:Icon(Icons.cameraswitch),label:'دوربین‌ها'),
          NavigationDestination(icon:Icon(Icons.notifications_active_outlined),selectedIcon:Icon(Icons.notifications_active),label:'رخدادها'),
          NavigationDestination(icon:Icon(Icons.settings_outlined),selectedIcon:Icon(Icons.settings),label:'تنظیمات'),
        ],
      ),
    ));
  }

  Widget _home() => ListView(padding:const EdgeInsets.all(16),children:[
    Container(padding:const EdgeInsets.all(18),decoration:BoxDecoration(
      gradient:const LinearGradient(colors:[Color(0xFF292D35),Color(0xFF171A20)]),
      borderRadius:BorderRadius.circular(20),border:Border.all(color:Colors.white10)),
      child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
        Row(children:[const Expanded(child:Text('مرکز نظارت هوشمند',style:TextStyle(fontSize:20,fontWeight:FontWeight.bold))),_statusDot()]),
        const SizedBox(height:6),Text(connection,style:const TextStyle(color:Colors.white60,fontSize:12)),
        const SizedBox(height:18),Row(children:[
          _metric('کل دوربین‌ها','${cameras.length}',Icons.videocam_outlined),
          const SizedBox(width:12),_metric('آنلاین','—',Icons.wifi_rounded),
          const SizedBox(width:12),_metric('هشدار امروز','۰',Icons.notifications_none),
        ]),
      ]),
    ),
    const SizedBox(height:20),
    Row(mainAxisAlignment:MainAxisAlignment.spaceBetween,children:[
      const Text('نمای زنده',style:TextStyle(fontSize:17,fontWeight:FontWeight.bold)),
      TextButton(onPressed:()=>setState(()=>selectedTab=1),child:const Text('همه دوربین‌ها')),
    ]),
    GridView.builder(shrinkWrap:true,physics:const NeverScrollableScrollPhysics(),itemCount:cameras.take(4).length,
      gridDelegate:const SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount:2,childAspectRatio:1.18,crossAxisSpacing:10,mainAxisSpacing:10),
      itemBuilder:(context,i)=>_previewCard(cameras[i])),
    const SizedBox(height:16),
    Container(padding:const EdgeInsets.all(14),decoration:BoxDecoration(color:panel,borderRadius:BorderRadius.circular(16)),
      child:const Row(children:[Icon(Icons.info_outline,color:brandRed),SizedBox(width:10),Expanded(child:Text('نسخه آزمایشی: تصویر زنده و تشخیص هوشمند پس از راه‌اندازی سرویس استریم و اتصال واقعی دستگاه فعال می‌شود.',style:TextStyle(fontSize:12,color:Colors.white70)))])),
  ]);

  Widget _metric(String label,String value,IconData icon)=>Expanded(child:Container(padding:const EdgeInsets.all(10),decoration:BoxDecoration(color:Colors.white.withOpacity(.05),borderRadius:BorderRadius.circular(14)),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Icon(icon,color:brandRed,size:19),const SizedBox(height:8),Text(value,style:const TextStyle(fontSize:21,fontWeight:FontWeight.bold)),Text(label,style:const TextStyle(fontSize:10,color:Colors.white60))])));
  Widget _statusDot()=>Row(children:[Container(width:8,height:8,decoration:const BoxDecoration(color:Color(0xFFFFB74D),shape:BoxShape.circle)),const SizedBox(width:6),const Text('TEST',style:TextStyle(color:Color(0xFFFFB74D),fontSize:10,fontWeight:FontWeight.bold))]);
  Widget _previewCard(CameraItem c)=>Container(decoration:BoxDecoration(color:panel,borderRadius:BorderRadius.circular(16),border:Border.all(color:Colors.white10)),clipBehavior:Clip.antiAlias,child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
    Expanded(child:Container(color:const Color(0xFF252A32),child:const Center(child:Icon(Icons.videocam_off_outlined,size:34,color:Colors.white24)))),
    Padding(padding:const EdgeInsets.all(9),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(c.name,style:const TextStyle(fontWeight:FontWeight.bold,fontSize:12),maxLines:1,overflow:TextOverflow.ellipsis),Text('${c.brand} • ${c.host}',style:const TextStyle(color:Colors.white54,fontSize:9),maxLines:1,overflow:TextOverflow.ellipsis)])),
  ]));

  Widget _cameraList()=>ListView(padding:const EdgeInsets.all(16),children:[
    Row(mainAxisAlignment:MainAxisAlignment.spaceBetween,children:[const Text('مدیریت دوربین‌ها',style:TextStyle(fontSize:19,fontWeight:FontWeight.bold)),Text('${cameras.length} دستگاه',style:const TextStyle(color:Colors.white54))]),
    const SizedBox(height:12),
    ...cameras.map((c)=>Card(child:ListTile(leading:Container(width:42,height:42,decoration:BoxDecoration(color:brandRed.withOpacity(.13),borderRadius:BorderRadius.circular(12)),child:const Icon(Icons.videocam,color:brandRed)),title:Text(c.name),subtitle:Text('${c.brand}  •  ${c.host}\n${c.location}',style:const TextStyle(fontSize:11)),isThreeLine:true,trailing:const Icon(Icons.chevron_left)))),
    const SizedBox(height:12),OutlinedButton.icon(onPressed:connecting?null:syncCameras,icon:const Icon(Icons.sync),label:Text(connecting?'در حال همگام‌سازی':'همگام‌سازی با سرور')),
  ]);

  Widget _events()=>ListView(padding:const EdgeInsets.all(16),children:[
    const Text('رخدادها و هشدارها',style:TextStyle(fontSize:19,fontWeight:FontWeight.bold)),const SizedBox(height:18),
    Container(padding:const EdgeInsets.all(16),decoration:BoxDecoration(color:panel,borderRadius:BorderRadius.circular(16)),child:const Column(children:[Icon(Icons.notifications_none,size:42,color:Colors.white38),SizedBox(height:10),Text('هنوز رخدادی دریافت نشده',style:TextStyle(color:Colors.white70)),SizedBox(height:5),Text('پس از اتصال دوربین‌ها و فعال‌سازی تحلیل، هشدارها اینجا نمایش داده می‌شوند.',textAlign:TextAlign.center,style:TextStyle(color:Colors.white38,fontSize:12))])),
  ]);

  Widget _settings()=>ListView(padding:const EdgeInsets.all(16),children:[
    const Text('تنظیمات برنامه',style:TextStyle(fontSize:19,fontWeight:FontWeight.bold)),const SizedBox(height:12),
    Card(child:ListTile(leading:const Icon(Icons.dns_outlined,color:brandRed),title:const Text('آدرس سرور مرکزی'),subtitle:Text(apiBase),trailing:const Icon(Icons.edit),onTap:editServer)),
    const Card(child:ListTile(leading:Icon(Icons.language,color:brandRed),title:Text('زبان'),subtitle:Text('فارسی (نسخه آزمایشی)'))),
    const Card(child:ListTile(leading:Icon(Icons.security,color:brandRed),title:Text('امنیت'),subtitle:Text('اطلاعات ورود دوربین در این نسخه موبایل ذخیره نمی‌شود.'))),
    const Card(child:ListTile(leading:Icon(Icons.info_outline,color:brandRed),title:Text('نسخه'),subtitle:Text('0.1.0 • Android Test'))),
    const SizedBox(height:10),FilledButton.icon(style:FilledButton.styleFrom(backgroundColor:brandRed),onPressed:syncCameras,icon:const Icon(Icons.link),label:const Text('بررسی اتصال به سرور')),
  ]);
}
