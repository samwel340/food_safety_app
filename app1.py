import streamlit as st
from supabase import create_client, Client
import os

# إعداد الاتصال بـ Supabase
url = "https://hbwpblhsvnjhjadtfktu.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhid3BibGhzdm5qaGphZHRma3R1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk4OTA4MTYsImV4cCI6MjA2NTQ2NjgxNn0.I_fxniVQzVbi-jogGWU3JJVeNqT1ETcnHdMetgBtHes"
supabase: Client = create_client(url, key)

# تنسيق الصفحة
st.set_page_config(page_title="الهيئة القومية لسلامة الغذاء", page_icon="✅", layout="wide")

# تنسيقات CSS رسمية بالأبيض والأخضر الفاتح
st.markdown("""
    <style>
        body {
            background-color: #f8fff8;
        }
        .title {
            color: #006400;
            text-align: center;
            font-size: 32px;
            font-weight: bold;
        }
        .subtitle {
            text-align: center;
            color: #004d00;
            font-size: 18px;
            margin-bottom: 30px;
        }
        .stButton>button {
            background-color: #00b050;
            color: white;
            font-weight: bold;
            border-radius: 8px;
            border: none;
            padding: 10px 20px;
        }
        .stButton>button:hover {
            background-color: #00803a;
            color: #fff;
        }
    </style>
""", unsafe_allow_html=True)

# شعار الهيئة
logo_path = os.path.join(os.path.dirname(__file__), "3.png")
st.image(logo_path, width=120)
st.markdown('<div class="title">الهيئة القومية لسلامة الغذاء</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">استعلام عن المنشاة /div>', unsafe_allow_html=True)

# خانة البحث
facility_code = st.text_input("أدخل كود المنشأة", placeholder="مثلاً: FAC12345")

if st.button("بحث"):
    if facility_code.strip() == "":
        st.warning("الرجاء إدخال كود المنشأة.")
    else:
        result = supabase.table("facility_visits").select("*").eq("facility_code", facility_code).execute()

        if result.data:
            record = result.data[0]
            st.success("✅ تم العثور على بيانات المنشأة")

            # عرض البيانات بشكل منسق
            cols = st.columns(2)
            with cols[0]:
                st.write("**اسم المنشأة:**", record.get("facility_name"))
                st.write("**الفرع:**", record.get("branch_name"))
                st.write("**المحافظة:**", record.get("governorate"))
                st.write("**العنوان:**", record.get("branch_address"))
                st.write("**النشاط:**", record.get("branch_activity"))
            with cols[1]:
                st.write("**عدد العاملين:**", record.get("employee_count"))
                st.write("**عدد الكروت الصحية:**", record.get("health_card_count"))
                st.write("**نوع الزيارة:**", record.get("visit_type"))
                st.write("**المفتشين:**", f"{record.get('inspector_1')} / {record.get('inspector_2')}")
                st.write("**التاريخ:**", record.get("visit_date"))

            # عرض الحالة النهائية
            st.subheader("التقييم النهائي")
            st.metric("النتيجة", f"{record.get('final_average', 'غير محدد')}")
            st.write("**الحالة النهائية:**", record.get("final_status"))

        else:
            st.error("لم يتم العثور على بيانات بهذا الكود.")
