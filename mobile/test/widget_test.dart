import 'package:flutter_test/flutter_test.dart';
import 'package:molido_cctv/main.dart';

void main() {
  testWidgets('dashboard starts and shows the Molido CCTV brand', (tester) async {
    await tester.pumpWidget(const MolidoCctvApp());
    expect(find.text('MOLIDO CCTV AI'), findsOneWidget);
    expect(find.text('DAHUA • MULTI-BRAND'), findsOneWidget);
  });

  testWidgets('four navigation destinations are available', (tester) async {
    await tester.pumpWidget(const MolidoCctvApp());
    expect(find.text('خانه'), findsOneWidget);
    expect(find.text('دوربین‌ها'), findsOneWidget);
    expect(find.text('رخدادها'), findsOneWidget);
    expect(find.text('تنظیمات'), findsOneWidget);
  });
}
