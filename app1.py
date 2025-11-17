import streamlit as st
import pandas as pd
import os
import requests
from PIL import Image
import io
import base64
import json
from urllib.parse import urlparse
from datetime import datetime

# إعداد الصفحة
st.set_page_config(
    page_title="الهيئة القومية لسلامة الغذاء",
    page_icon="",
    layout="wide"
)

# تنسيق متقدم CSS
st.markdown("""
    <style>
    .main {
        background-color: #f8fff8;
        padding: 20px;
        border-radius: 15px;
    }
    .header-container {
        text-align: center;
        padding: 10px;
        background: linear-gradient(135deg, #006b3c, #009950);
        color: white;
        border-radius: 15px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 20px;
    }
    .header-text {
        flex: 1;
    }
    .logo-container {
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .facility-card {
        border: 2px solid #006b3c;
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        background: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .image-container {
        border: 2px dashed #006b3c;
        border-radius: 10px;
        padding: 15px;
        background: #f9f9f9;
        text-align: center;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .stButton>button {
        background-color: #006b3c;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #004d29;
        color: white;
    }
    .rating-good {
        color: #28a745;
        font-weight: bold;
    }
    .rating-average {
        color: #ffc107;
        font-weight: bold;
    }
    .rating-poor {
        color: #dc3545;
        font-weight: bold;
    }
    .search-box {
        background: white;
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #006b3c;
        text-align: center;
        margin-bottom: 20px;
    }
    @media (max-width: 768px) {
        .header-container {
            flex-direction: column;
            text-align: center;
        }
    }
    </style>
""", unsafe_allow_html=True)

# دالة لتحميل وعرض الشعار
def load_logo():
    """تحميل وعرض شعار الهيئة"""
    try:
        logo_path = os.path.join(os.path.dirname(__file__), "3.png")
        if os.path.exists(logo_path):
            return logo_path
        else:
            st.warning("⚠️ لم يتم العثور على ملف الشعار")
            return None
    except Exception as e:
        st.error(f"❌ خطأ في تحميل الشعار: {e}")
        return None

# الهيدر الرئيسي مع الشعار
logo_path = load_logo()

if logo_path:
    st.markdown(f"""
        <div class="header-container">
            <div class="logo-container">
                <img src="{logo_path}" width="100" style="border-radius: 10px;">
            </div>
            <div class="header-text">
                <h1>🏢 الهيئة القومية لسلامة الغذاء</h1>
                <h3>نظام إدارة المنشآت الغذائية</h3>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <div class="header-container">
            <div class="header-text">
                <h1> الهيئة القومية لسلامة الغذاء</h1>
                <h3>نظام إدارة المنشآت الغذائية</h3>
            </div>
        </div>
    """, unsafe_allow_html=True)

# دالة محسنة لتحميل الصور
def smart_image_loader(image_url):
    """دالة ذكية لتحميل الصور من مختلف المصادر"""
    if not image_url or pd.isna(image_url):
        return None, "لا يوجد رابط صورة"
    
    clean_url = str(image_url).strip()
    
    # معالجة روابط Google Drive
    if 'drive.google.com' in clean_url:
        if '/file/d/' in clean_url:
            file_id = clean_url.split('/file/d/')[1].split('/')[0]
            clean_url = f"https://drive.google.com/uc?export=view&id={file_id}"
        elif 'id=' in clean_url:
            file_id = clean_url.split('id=')[1].split('&')[0]
            clean_url = f"https://drive.google.com/uc?export=view&id={file_id}"
    
    # معالجة روابط Dropbox
    if 'dropbox.com' in clean_url:
        if '?dl=0' in clean_url:
            clean_url = clean_url.replace('?dl=0', '?dl=1')
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(clean_url, timeout=15, headers=headers)
        
        if response.status_code == 200:
            # التحقق من أن المحتوى هو صورة
            if 'image' in response.headers.get('content-type', ''):
                image = Image.open(io.BytesIO(response.content))
                return image, "نجح"
            else:
                return None, "الرابط لا يشير إلى صورة"
        else:
            return None, f"خطأ في الخادم: {response.status_code}"
            
    except Exception as e:
        return None, f"خطأ في التحميل: {str(e)}"

def get_rating_color(rating):
    """إرجاع لون التقييم بناءً على القيمة"""
    if pd.isna(rating) or rating == '':
        return "rating-average"
    try:
        rating_value = float(str(rating))
        if rating_value >= 8:
            return "rating-good"
        elif rating_value >= 5:
            return "rating-average"
        else:
            return "rating-poor"
    except:
        return "rating-average"

# تحميل البيانات من Google Sheets
@st.cache_data(ttl=300)  # خزن البيانات لمدة 5 دقائق
def load_data():
    """تحميل البيانات من Google Sheets"""
    try:
        sheet_url = "https://docs.google.com/spreadsheets/d/11Lm7z0i1iybr4Pj1go7MzvS2228ZSjJs32QzLUrdbzA/export?format=csv"
        data = pd.read_csv(sheet_url)
        data.columns = data.columns.str.strip()
        
        # تنظيف الأعمدة
        if 'رفع الصورة' in data.columns:
            data['رفع الصورة'] = data['رفع الصورة'].fillna('').astype(str)
        if 'تقيم المنشاة' in data.columns:
            data['تقيم المنشاة'] = data['تقيم المنشاة'].fillna('').astype(str)
        if 'اسم الفتش' in data.columns:
            data['اسم الفتش'] = data['اسم الفتش'].fillna('').astype(str)
        if 'كود لمفتش' in data.columns:
            data['كود لمفتش'] = data['كود لمفتش'].fillna('').astype(str)
            
        return data
    except Exception as e:
        st.error(f"❌ خطأ في تحميل البيانات: {e}")
        return pd.DataFrame()

data = load_data()

# تبويبات التطبيق
tab1, tab2, tab3 = st.tabs([
    "🔍 البحث بكود المنشأة", 
    "🖼️ معرض الصور", 
    "⚙️ الإعدادات والمساعدة"
])

with tab1:
    st.header("🔍 البحث بكود المنشأة")
    
    # مربع البحث المخصص
    st.markdown("""
        <div class="search-box">
            <h3>🔍 أدخل كود المنشأة للبحث</h3>
            <p>اكتب الكود الخاص بالمنشأة للعثور على معلوماتها</p>
        </div>
    """, unsafe_allow_html=True)
    
    # مربع البحث بكود المنشأة فقط
    facility_code = st.text_input(
        "كود المنشأة:",
        placeholder="أدخل الكود هنا...",
        key="facility_code_search"
    )
    
    if facility_code:
        # البحث فقط في عمود الكود
        filtered_data = data[data['الكود'].astype(str).str.contains(facility_code, case=False, na=False)]
        
        if len(filtered_data) == 0:
            st.warning("⚠️ لم يتم العثور على منشأة بهذا الكود")
            st.info("💡 تأكد من صحة الكود المدخل أو جرب البحث في معرض الصور")
        else:
            st.success(f"🎉 تم العثور على {len(filtered_data)} نتيجة للكود: {facility_code}")
            
            for idx, row in filtered_data.iterrows():
                with st.container():
                    st.markdown('<div class="facility-card">', unsafe_allow_html=True)
                    
                    col_img, col_info = st.columns([1, 2])
                    
                    with col_img:
                        image_url = row.get('رفع الصورة', '')
                        facility_name = row.get('اسم المنشاة', 'غير معروف')
                        
                        if image_url and image_url.strip():
                            image, status = smart_image_loader(image_url)
                            if image:
                                st.image(image, use_container_width=True)
                                st.caption("📷 صورة المنشأة")
                            else:
                                st.markdown(f"""
                                    <div class="image-container">
                                        <h3>🖼️</h3>
                                        <p>تعذر تحميل الصورة</p>
                                        <small>{status}</small>
                                        <br>
                                        <a href="{image_url}" target="_blank">🔗 فتح الرابط</a>
                                    </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                                <div class="image-container">
                                    <h3>📷</h3>
                                    <p>لا توجد صورة</p>
                                </div>
                            """, unsafe_allow_html=True)
                    
                    with col_info:
                        st.subheader(f"🏢 {row.get('اسم المنشاة', 'غير معروف')}")
                        
                        # استخدام 3 أعمدة لعرض جميع المعلومات
                        info_cols = st.columns(3)
                        
                        with info_cols[0]:
                            st.write(f"**📋 كود المنشأة:** {row.get('الكود', 'غير معروف')}")
                            st.write(f"**🏷️ نوع المنشأة:** {row.get('نوع المنشاة', 'غير معروف')}")
                            st.write(f"**📍 العنوان:** {row.get('العنوان', 'غير معروف')}")
                            st.write(f"**📅 التاريخ:** {row.get('Timestamp', 'غير معروف')}")
                        
                        with info_cols[1]:
                            st.write(f"**👤 اسم المفتش:** {row.get('اسم الفتش', 'غير معروف')}")
                            st.write(f"**🆔 كود المفتش:** {row.get('كود لمفتش', 'غير معروف')}")
                            if image_url and image_url.strip():
                                st.write(f"**🔗 رابط الصورة:** [فتح]({image_url})")
                        
                        with info_cols[2]:
                            # تقييم المنشأة
                            rating = row.get('تقيم المنشاة', '')
                            rating_class = get_rating_color(rating)
                            if rating and str(rating).strip():
                                st.markdown(f"<p class='{rating_class}'>**⭐ تقييم المنشأة:** {rating}</p>", unsafe_allow_html=True)
                            else:
                                st.write("**⭐ تقييم المنشأة:** غير متوفر")
                            
                            # معلومات إضافية
                            st.write("**📊 حالة المنشأة:** نشطة")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("🔍 ابدأ بإدخال كود المنشأة للبحث...")

with tab2:
    st.header("🖼️ معرض صور المنشآت")
    
    # تصفية المنشآت التي تحتوي على صور
    facilities_with_images = data[data['رفع الصورة'].notna() & (data['رفع الصورة'] != '')]
    
    if len(facilities_with_images) == 0:
        st.info("📭 لا توجد منشآت تحتوي على صور حالياً.")
    else:
        st.success(f"🖼️ تم العثور على {len(facilities_with_images)} منشأة تحتوي على صور")
        
        # خيارات التصفية
        col1, col2 = st.columns(2)
        with col1:
            items_per_row = st.selectbox("عدد الصور في الصف:", [2, 3, 4])
        with col2:
            search_gallery = st.text_input("🔍 بحث بالكود في المعرض:", placeholder="أدخل كود المنشأة...")
        
        # تطبيق البحث إذا وجد
        display_facilities = facilities_with_images
        if search_gallery:
            display_facilities = facilities_with_images[
                facilities_with_images['الكود'].astype(str).str.contains(search_gallery, case=False, na=False)
            ]
            if len(display_facilities) == 0:
                st.warning("⚠️ لم يتم العثور على منشآت بهذا الكود في المعرض")
            else:
                st.info(f"عرض {len(display_facilities)} منشأة من أصل {len(facilities_with_images)}")
        
        # عرض الصور في grid
        cols = st.columns(items_per_row)
        
        for idx, (_, row) in enumerate(display_facilities.iterrows()):
            with cols[idx % items_per_row]:
                image_url = row['رفع الصورة']
                facility_name = row['اسم المنشاة']
                facility_code = row.get('الكود', 'غير معروف')
                
                image, status = smart_image_loader(image_url)
                if image:
                    st.image(image, use_container_width=True)
                    st.write(f"**{facility_name}**")
                    st.caption(f"**الكود:** {facility_code}")
                    st.caption(f"النوع: {row.get('نوع المنشاة', 'غير معروف')}")
                    st.caption(f"المفتش: {row.get('اسم الفتش', 'غير معروف')}")
                    
                    # عرض التقييم مع لون
                    rating = row.get('تقيم المنشاة', '')
                    if rating and str(rating).strip():
                        rating_class = get_rating_color(rating)
                        st.markdown(f"<p class='{rating_class}'>التقييم: {rating}</p>", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div style="border: 1px dashed #ccc; padding: 20px; text-align: center; border-radius: 10px;">
                            <h3>📷 {facility_name}</h3>
                            <p><strong>الكود:</strong> {facility_code}</p>
                            <p>تعذر تحميل الصورة</p>
                            <small>{status}</small>
                            <br>
                            <a href="{image_url}" target="_blank">🔗 فتح الرابط</a>
                        </div>
                    """, unsafe_allow_html=True)

with tab3:
    st.header("⚙️ الإعدادات والمساعدة")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🛠️ أدوات الصيانة")
        
        if st.button("🔄 تحديث البيانات"):
            st.cache_data.clear()
            st.rerun()
            st.success("✅ تم تحديث البيانات بنجاح")
        
        if st.button("🔍 فحص جميع الصور"):
            with st.spinner("جاري فحص جميع الصور..."):
                total = len(data)
                working = 0
                broken = 0
                no_images = 0
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, (_, row) in enumerate(data.iterrows()):
                    status_text.text(f"جاري فحص {idx+1} من {total}")
                    progress_bar.progress((idx + 1) / total)
                    
                    image_url = row.get('رفع الصورة', '')
                    if not image_url or image_url.strip() == '':
                        no_images += 1
                    else:
                        _, status = smart_image_loader(image_url)
                        if "نجح" in status:
                            working += 1
                        else:
                            broken += 1
                
                st.success(f"✅ الصور العاملة: {working}")
                st.error(f"❌ الصور التالفة: {broken}")
                st.info(f"📭 بدون صور: {no_images}")
                st.info(f"📊 إجمالي المنشآت: {total}")
    
    with col2:
        st.subheader("📊 إحصائيات النظام")
        
        total_facilities = len(data)
        with_images = len(data[data['رفع الصورة'].notna() & (data['رفع الصورة'] != '')])
        without_images = total_facilities - with_images
        
        # إحصائيات المفتشين
        inspectors = data['اسم الفتش'].nunique() if 'اسم الفتش' in data.columns else 0
        unique_codes = data['الكود'].nunique() if 'الكود' in data.columns else 0
        
        st.metric("إجمالي المنشآت", total_facilities)
        st.metric("المنشآت ذات الصور", with_images)
        st.metric("عدد المفتشين", inspectors)
        st.metric("عدد الأكواد الفريدة", unique_codes)
        
        if total_facilities > 0:
            percentage_with_images = (with_images / total_facilities) * 100
            st.metric("نسبة المنشآت ذات الصور", f"{percentage_with_images:.1f}%")
    
    st.subheader("📖 دليل الاستخدام")
    
    with st.expander("كيفية استخدام النظام"):
        st.write("""
        **🔍 البحث بكود المنشأة:**
        - اكتب كود المنشأة في مربع البحث
        - سيتم عرض جميع المعلومات الخاصة بالمنشأة
        - إذا لم تظهر نتائج، تأكد من صحة الكود
        
        **🖼️ معرض الصور:**
        - عرض جميع المنشآت التي تحتوي على صور
        - يمكنك البحث بالكود داخل المعرض
        - يمكنك تغيير عدد الصور في كل صف
        
        **الحقول المعروضة:**
        - ✅ اسم المنشأة
        - ✅ نوع المنشأة  
        - ✅ العنوان
        - ✅ الكود
        - ✅ صورة المنشأة
        - ✅ اسم المفتش
        - ✅ كود المفتش
        - ✅ تقييم المنشأة
        - ✅ تاريخ التسجيل
        """)
    
    with st.expander("استكشاف الأخطاء وإصلاحها"):
        st.write("""
        **إذا لم تظهر المنشأة:**
        - تأكد من صحة كود المنشأة المدخل
        - تأكد من اتصال الإنترنت
        - استخدم زر تحديث البيانات
        
        **إذا لم تظهر الصور:**
        - الروابط قد تكون قديمة أو غير صالحة
        - استخدم أداة فحص الصور لمشاهدة الحالة
        - يمكنك فتح الرابط مباشرة في متصفح جديد
        
        **لتحسين الأداء:**
        - استخدم تحديث البيانات لتحميل أحدث المعلومات
        - اختر عدد مناسب من الصور في الصف الواحد
        """)

# تذييل الصفحة مع الشعار الصغير
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if logo_path:
        st.image(logo_path, width=80)
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "© 2024 الهيئة القومية لسلامة الغذاء - جميع الحقوق محفوظة"
        "</div>",
        unsafe_allow_html=True
    )
