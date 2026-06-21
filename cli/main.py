#!/usr/bin/env python3
import sys
import argparse

from toll.engine.content_machine import ContentMachine
from toll.engine.prompt_gen import PromptGenerator
from toll.engine.reports import Reports
from toll.core.ai import AI

def main():
    parser = argparse.ArgumentParser(prog="تول", description="مساعدك الشخصي الموحد")
    parser.add_argument("engine", nargs="?", help="الأداة: content, prompt, report, status")
    parser.add_argument("task", nargs="*", default=[], help="المهمة أو النص")
    parser.add_argument("--slides", type=int, default=5, help="عدد الشرائح (للعرض)")
    parser.add_argument("--platform", default="عام", help="المنصة (للمنشور)")

    args = parser.parse_args()
    text = " ".join(args.task) or "افتراضي"

    if not args.engine or args.engine == "help":
        print("""
🧠 تول — مساعدك الشخصي الموحد

الاستخدام:
  تول <أداة> <المهمة> [خيارات]

الأدوات:
  content    ← Carousel HTML + منشورات
  prompt     ← توليد برومبتات
  report     ← تقارير HTML
  present    ← عروض تقديمية HTML
  status     ← حالة الـ AI والـ limits
  help       ← هذه الرسالة

أمثلة:
  تول content "منتج جديد"
  تول prompt "برومبت تسويق"
  تول report "ملخص المشروع"
  تول present "خطة العمل" --slides 7
  تول content "فكرة" --platform تويتر
  تول status
        """)
        return

    if args.engine == "status":
        ai = AI()
        s = ai.limit_status()
        print("📊 حالة الـ AI:")
        for p, v in s.items():
            icon = "✅" if v["can_use"] else "❌"
            print(f"  {icon} {p}: {v['remaining']} طلب متبقي")
        return

    try:
        if args.engine == "content":
            cm = ContentMachine()
            print(cm.carousel(text))
            print()
            print(cm.social_post(args.platform, text))

        elif args.engine == "prompt":
            pg = PromptGenerator()
            print(pg.generate(text))

        elif args.engine == "report":
            r = Reports()
            print(r.report(text))

        elif args.engine == "present":
            r = Reports()
            print(r.presentation(text, args.slides))

        else:
            print(f"❌ أداة غير معروفة: {args.engine}")
            print("اكتب: تول help")

    except Exception as e:
        print(f"❌ خطأ: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
