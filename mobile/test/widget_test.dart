import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:molido_cctv/main.dart';

Widget testDashboard() => MolidoCctvApp(
  homeOverride: DashboardPage(
    token: 'test-token',
    role: 'manager',
    initialApiBase: 'http://10.0.2.2:8000',
    onLogout: () async {},
  ),
);

void main() {
  testWidgets('dashboard starts and shows the Molido CCTV brand', (tester) async {
    await tester.pumpWidget(testDashboard());
    expect(find.text('MOLIDO CCTV AI'), findsOneWidget);
    expect(find.text('DAHUA • MULTI-BRAND'), findsOneWidget);
  });

  testWidgets('four navigation destinations are available', (tester) async {
    await tester.pumpWidget(testDashboard());
    expect(find.text('خانه'), findsOneWidget);
    expect(find.text('دوربین‌ها'), findsOneWidget);
    expect(find.text('رخدادها'), findsOneWidget);
    expect(find.text('تنظیمات'), findsOneWidget);
  });
}
