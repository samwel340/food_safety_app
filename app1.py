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
    .white-list-good {
        background: #d4edda;
        color: #155724;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .white-list-pending {
        background: #fff3cd;
        color: #856404;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .white-list-bad {
        background: #f8d7da;
        color: #721c24;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
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

# دالة لتحديد لون حالة القائمة البيضاء
def get_white_list_status(status):
    """إرجاع تنسيق الحالة بناءً على الموقف بالقائمة البيضاء"""
    if pd.isna(status) or status == '':
        return "white-list-pending", "قيد المراجعة"
    
    status_str = str(status).strip().lower()
    
    if any(word in status_str for word in ['مطابق', 'جيد', 'مقبول', 'نعم', 'موافق']):
        return "white-list-good", "مطابق"
    elif any(word in status_str for word in ['غير مطابق', 'رفض', 'لا', 'مرفوض']):
        return "white-list-bad", "غير مطابق"
    else:
        return "white-list-pending", "قيد المراجعة"

# تحميل البيانات من Google Sheets
@st.cache_data(ttl=300)  # خزن البيانات لمدة 5 دقائق
def load_data():
    """تحميل البيانات من Google Sheets"""
    try:
        # الرابط الجديد
        sheet_url = "https://docs.google.com/spreadsheets/d/1nV6ynld1ogJ36qSuHryKBB-Cs8qBsYRuH0adS9SXzEA/export?format=csv"
        data = pd.read_csv(sheet_url)
        
        # عرض الأعمدة المتاحة للمساعدة في التصحيح
        st.info(f"📊 الأعمدة المتاحة في البيانات: {list(data.columns)}")
        
        # تنظيف أسماء الأعمدة (إزالة المسافات الزائدة)
        data.columns = data.columns.str.strip()
        
        st.success(f"✅ تم تحميل {len(data)} سجل بنجاح")
        
        return data
        
    except Exception as e:
        st.error(f"❌ خطأ في تحميل البيانات: {e}")
        return pd.DataFrame()

data = load_data()

# التحقق من وجود الأعمدة المطلوبة
def check_required_columns():
    """التحقق من وجود الأعمدة المطلوبة في البيانات"""
    required_columns = [
        'الكود الجديد', 'فئة المنشأة', 'اسم المنشأة بالبطاقة الضريبية',
        'اسم المنشأة على اللافتة', 'عنوان المنشأة (المحافظة)',
        'عنوان المنشأة (المنطقة / المدينة)', 'عنوان المنشأة (تفصيلياً)',
        'الموقف بالقائمة البيضاء'
    ]
    
    missing_columns = []
    available_columns = []
    
    for col in required_columns:
        if col in data.columns:
            available_columns.append(col)
        else:
            missing_columns.append(col)
    
    return available_columns, missing_columns

# تبويبات التطبيق
tab1, tab2 = st.tabs([
    "🔍 البحث بكود المنشأة", 
    "📊 الإحصائيات والمساعدة"
])

with tab1:
    st.header("🔍 البحث بكود المنشأة")
    
    # التحقق من الأعمدة المتاحة
    available_columns, missing_columns = check_required_columns()
    
    if missing_columns:
        st.warning(f"⚠️ الأعمدة المفقودة: {missing_columns}")
    
    # إذا لم يكن عمود 'الكود الجديد' موجوداً، نستخدم أول عمود كبديل
    search_column = 'الكود الجديد'
    if search_column not in data.columns:
        if len(data.columns) > 0:
            search_column = data.columns[0]
            st.warning(f"⚠️ استخدام العمود '{search_column}' للبحث بدلاً من 'الكود الجديد'")
        else:
            st.error("❌ لا توجد أعمدة في البيانات للبحث")
            search_column = None
    
    # مربع البحث المخصص
    st.markdown("""
        <div class="search-box">
            <h3>🔍 أدخل كود المنشأة للبحث</h3>
            <p>اكتب الكود الجديد الخاص بالمنشأة للعثور على معلوماتها</p>
        </div>
    """, unsafe_allow_html=True)
    
    if search_column:
        # مربع البحث بالكود الجديد فقط
        facility_code = st.text_input(
            f"{search_column}:",
            placeholder=f"أدخل {search_column} هنا...",
            key="facility_code_search"
        )
        
        if facility_code:
            # البحث في العمود المحدد
            try:
                filtered_data = data[data[search_column].astype(str).str.contains(facility_code, case=False, na=False)]
                
                if len(filtered_data) == 0:
                    st.warning("⚠️ لم يتم العثور على منشأة بهذا الكود")
                    st.info("💡 تأكد من صحة الكود المدخل")
                else:
                    st.success(f"🎉 تم العثور على {len(filtered_data)} نتيجة للكود: {facility_code}")
                    
                    for idx, row in filtered_data.iterrows():
                        with st.container():
                            st.markdown('<div class="facility-card">', unsafe_allow_html=True)
                            
                            # عرض المعلومات الأساسية
                            facility_name = row.get('اسم المنشأة بالبطاقة الضريبية', 
                                          row.get('اسم المنشأة على اللافتة', 
                                          f"منشأة {row.get(search_column, 'غير معروف')}"))
                            
                            st.subheader(f"🏢 {facility_name}")
                            
                            # استخدام 3 أعمدة لعرض جميع المعلومات
                            info_cols = st.columns(3)
                            
                            with info_cols[0]:
                                st.write(f"**📋 {search_column}:** {row.get(search_column, 'غير معروف')}")
                                
                                if 'فئة المنشأة' in row:
                                    st.write(f"**🏷️ فئة المنشأة:** {row.get('فئة المنشأة', 'غير معروف')}")
                                
                                # حالة القائمة البيضاء
                                if 'الموقف بالقائمة البيضاء' in row:
                                    white_list_status = row.get('الموقف بالقائمة البيضاء', '')
                                    status_class, status_text = get_white_list_status(white_list_status)
                                    st.markdown(f"**📊 الموقف بالقائمة البيضاء:** <span class='{status_class}'>{status_text}</span>", unsafe_allow_html=True)
                            
                            with info_cols[1]:
                                # تجميع العنوان
                                address_parts = []
                                if 'عنوان المنشأة (المحافظة)' in row and row.get('عنوان المنشأة (المحافظة)', '').strip():
                                    address_parts.append(f"المحافظة: {row['عنوان المنشأة (المحافظة)']}")
                                if 'عنوان المنشأة (المنطقة / المدينة)' in row and row.get('عنوان المنشأة (المنطقة / المدينة)', '').strip():
                                    address_parts.append(f"المنطقة: {row['عنوان المنشأة (المنطقة / المدينة)']}")
                                if 'عنوان المنشأة (تفصيلياً)' in row and row.get('عنوان المنشأة (تفصيلياً)', '').strip():
                                    address_parts.append(f"التفاصيل: {row['عنوان المنشأة (تفصيلياً)']}")
                                
                                if address_parts:
                                    full_address = " - ".join(address_parts)
                                    st.write(f"**📍 العنوان:** {full_address}")
                                else:
                                    st.write("**📍 العنوان:** غير متوفر")
                            
                            with info_cols[2]:
                                # معلومات إضافية
                                st.write("**📅 تاريخ التسجيل:** غير محدد")
                                st.write("**🔍 حالة السجل:** نشط")
                                
                                # عرض القيمة الفعلية للقائمة البيضاء إذا كانت موجودة
                                if 'الموقف بالقائمة البيضاء' in row and row.get('الموقف بالقائمة البيضاء', '').strip():
                                    st.write(f"**📝 تفاصيل القائمة البيضاء:** {row.get('الموقف بالقائمة البيضاء', '')}")
                                
                                # عرض اسم المنشأة على اللافتة إذا كان مختلفاً
                                if ('اسم المنشأة على اللافتة' in row and 
                                    'اسم المنشأة بالبطاقة الضريبية' in row and
                                    row.get('اسم المنشأة على اللافتة', '') != row.get('اسم المنشأة بالبطاقة الضريبية', '') and 
                                    row.get('اسم المنشأة على اللافتة', '').strip()):
                                    st.write(f"**🏷️ اسم اللافتة:** {row.get('اسم المنشأة على اللافتة', '')}")
                            
                            st.markdown('</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"❌ خطأ في البحث: {e}")
                st.info("💡 جرب استخدام كود بحث مختلف أو تحقق من تنسيق البيانات")
        else:
            st.info("🔍 ابدأ بإدخال كود المنشأة للبحث...")
    else:
        st.error("❌ لا يمكن إجراء البحث - لا توجد أعمدة متاحة في البيانات")

with tab2:
    st.header("📊 الإحصائيات والمساعدة")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🛠️ أدوات الصيانة")
        
        if st.button("🔄 تحديث البيانات"):
            st.cache_data.clear()
            st.rerun()
            st.success("✅ تم تحديث البيانات بنجاح")
        
        if st.button("📋 عرض عينة من البيانات"):
            st.subheader("عينة من البيانات المتاحة")
            if len(data) > 0:
                # عرض أول 5 صفوف مع جميع الأعمدة
                st.dataframe(data.head(), use_container_width=True)
            else:
                st.warning("لا توجد بيانات متاحة للعرض")
    
    with col2:
        st.subheader("📊 إحصائيات النظام")
        
        total_facilities = len(data)
        
        # إحصائيات القائمة البيضاء إذا كان العمود موجوداً
        if 'الموقف بالقائمة البيضاء' in data.columns:
            white_list_data = data['الموقف بالقائمة البيضاء'].fillna('')
            compliant = white_list_data.str.contains('مطابق|جيد|مقبول|نعم|موافق', case=False, na=False).sum()
            non_compliant = white_list_data.str.contains('غير مطابق|رفض|لا|مرفوض', case=False, na=False).sum()
            pending = total_facilities - compliant - non_compliant
        else:
            compliant = 0
            non_compliant = 0
            pending = total_facilities
        
        unique_categories = data['فئة المنشأة'].nunique() if 'فئة المنشأة' in data.columns else 0
        
        # عدد الأكواد الفريدة باستخدام عمود البحث
        search_column_actual = search_column if search_column else (data.columns[0] if len(data.columns) > 0 else None)
        unique_codes = data[search_column_actual].nunique() if search_column_actual else 0
        
        st.metric("إجمالي المنشآت", total_facilities)
        st.metric("المنشآت المطابقة", compliant)
        st.metric("المنشآت غير المطابقة", non_compliant)
        st.metric("قيد المراجعة", pending)
        st.metric("عدد الفئات", unique_categories)
        st.metric("عدد الأكواد الفريدة", unique_codes)
        
        # عرض الأعمدة المتاحة والمفقودة
        with st.expander("تفاصيل الأعمدة"):
            st.write("**✅ الأعمدة المتاحة:**", available_columns)
            if missing_columns:
                st.write("**❌ الأعمدة المفقودة:**", missing_columns)
    
    st.subheader("📖 دليل الاستخدام")
    
    with st.expander("كيفية استخدام النظام"):
        st.write("""
        **🔍 البحث بكود المنشأة:**
        - اكتب الكود الجديد للمنشأة في مربع البحث
        - سيتم عرض جميع المعلومات الخاصة بالمنشأة
        - إذا لم تظهر نتائج، تأكد من صحة الكود
        
        **الحقول المعروضة:**
        - ✅ الكود الجديد
        - ✅ فئة المنشأة  
        - ✅ اسم المنشأة بالبطاقة الضريبية
        - ✅ اسم المنشأة على اللافتة
        - ✅ العنوان (المحافظة، المنطقة، التفاصيل)
        - ✅ الموقف بالقائمة البيضاء
        
        **ألوان حالة القائمة البيضاء:**
        - 🟢 **أخضر**: منشأة مطابقة
        - 🟡 **أصفر**: قيد المراجعة
        - 🔴 **أحمر**: غير مطابقة
        """)
    
    with st.expander("استكشاف الأخطاء وإصلاحها"):
        st.write("""
        **إذا لم تظهر المنشأة:**
        - تأكد من صحة الكود الجديد المدخل
        - تأكد من اتصال الإنترنت
        - استخدم زر تحديث البيانات
        
        **إذا كانت البيانات غير مكتملة:**
        - بعض الحقول قد تكون فارغة في البيانات الأساسية
        - يمكنك الرجوع إلى المصدر الأصلي للبيانات
        
        **لتحسين الأداء:**
        - استخدم تحديث البيانات لتحميل أحدث المعلومات
        - تأكد من إدخال الكود بالكامل وبشكل صحيح
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
