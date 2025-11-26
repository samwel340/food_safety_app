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
    .stButton>button {
        background-color: #006b3c;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
    }
    .column-badge {
        background: #e9ecef;
        padding: 2px 8px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 0.9em;
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

# تحميل البيانات من Google Sheets
@st.cache_data(ttl=300)
def load_data():
    """تحميل البيانات من Google Sheets"""
    try:
        sheet_url = "https://docs.google.com/spreadsheets/d/1nV6ynld1ogJ36qSuHryKBB-Cs8qBsYRuH0adS9SXzEA/export?format=csv"
        data = pd.read_csv(sheet_url)
        
        # تنظيف أسماء الأعمدة
        data.columns = data.columns.str.strip()
        
        return data
        
    except Exception as e:
        st.error(f"❌ خطأ في تحميل البيانات: {e}")
        return pd.DataFrame()

data = load_data()

# دالة للعثور على أفضل عمود للبحث
def find_best_search_column(data):
    """العثور على أفضل عمود للبحث بناءً على الأعمدة المتوقعة"""
    possible_columns = [
        'الكود الجديد', 'الكود', 'كود', 'رقم', 'ID', 'Code', 'code',
        'كود المنشأة', 'رقم المنشأة'
    ]
    
    for col in possible_columns:
        if col in data.columns:
            return col
    
    # إذا لم نجد أي عمود من القائمة، نستخدم أول عمود نصي
    for col in data.columns:
        if data[col].dtype == 'object':
            return col
    
    # إذا فشل كل شيء، نستخدم أول عمود
    return data.columns[0] if len(data.columns) > 0 else None

# دالة لتصنيف الأعمدة
def classify_columns(data):
    """تصنيف الأعمدة حسب نوعها"""
    column_categories = {
        'codes': [],
        'names': [],
        'addresses': [],
        'types': [],
        'statuses': [],
        'dates': [],
        'other': []
    }
    
    name_keywords = ['اسم', 'name', 'Title', 'title', 'مسمى', 'شركة', 'منشأة']
    code_keywords = ['كود', 'code', 'رقم', 'id', 'ID', 'رمز']
    address_keywords = ['عنوان', 'address', 'موقع', 'مكان', 'محافظة', 'مدينة', 'منطقة']
    type_keywords = ['نوع', 'type', 'فئة', 'category', 'تصنيف']
    status_keywords = ['حالة', 'status', 'موقف', 'قائمة', 'بيضاء', 'نتيجة']
    date_keywords = ['تاريخ', 'date', 'وقت', 'time']
    
    for col in data.columns:
        col_lower = col.lower()
        
        if any(keyword in col_lower for keyword in code_keywords):
            column_categories['codes'].append(col)
        elif any(keyword in col_lower for keyword in name_keywords):
            column_categories['names'].append(col)
        elif any(keyword in col_lower for keyword in address_keywords):
            column_categories['addresses'].append(col)
        elif any(keyword in col_lower for keyword in type_keywords):
            column_categories['types'].append(col)
        elif any(keyword in col_lower for keyword in status_keywords):
            column_categories['statuses'].append(col)
        elif any(keyword in col_lower for keyword in date_keywords):
            column_categories['dates'].append(col)
        else:
            column_categories['other'].append(col)
    
    return column_categories

# تبويبات التطبيق
tab1, tab2, tab3 = st.tabs([
    "🔍 البحث", 
    "📊 عرض البيانات",
    "⚙️ الإعدادات"
])

with tab1:
    st.header("🔍 البحث في المنشآت")
    
    if data.empty:
        st.error("❌ لا توجد بيانات متاحة للبحث")
    else:
        # تصنيف الأعمدة
        column_categories = classify_columns(data)
        
        # عرض معلومات عن الأعمدة
        st.info(f"📁 تم تحميل {len(data)} سجل مع {len(data.columns)} عمود")
        
        # اختيار عمود البحث
        search_column = find_best_search_column(data)
        
        if not column_categories['codes']:
            st.warning(f"⚠️ لم يتم العثور على عمود أكواد واضح. سيتم استخدام العمود: **{search_column}** للبحث")
        
        # مربع البحث
        st.markdown("""
            <div class="search-box">
                <h3>🔍 أدخل كود أو اسم المنشأة للبحث</h3>
                <p>ابحث باستخدام أي معرِّف أو اسم للمنشأة</p>
            </div>
        """, unsafe_allow_html=True)
        
        search_term = st.text_input(
            f"بحث في عمود '{search_column}':",
            placeholder="أدخل كود أو اسم المنشأة...",
            key="search_input"
        )
        
        if search_term:
            # البحث في العمود المحدد
            try:
                filtered_data = data[data[search_column].astype(str).str.contains(search_term, case=False, na=False)]
                
                if len(filtered_data) == 0:
                    st.warning("⚠️ لم يتم العثور على نتائج تطابق البحث")
                    
                    # اقتراح بحث في أعمدة أخرى
                    st.info("💡 جرب البحث في:")
                    for col in data.columns[:3]:  # عرض أول 3 أعمدة كبدائل
                        if col != search_column:
                            st.write(f"- العمود: `{col}`")
                else:
                    st.success(f"🎉 تم العثور على {len(filtered_data)} نتيجة")
                    
                    for idx, row in filtered_data.iterrows():
                        with st.container():
                            st.markdown('<div class="facility-card">', unsafe_allow_html=True)
                            
                            # العثور على أفضل عمود للاسم
                            facility_name = "منشأة غير معروفة"
                            if column_categories['names']:
                                facility_name = row[column_categories['names'][0]]
                            elif search_column in row:
                                facility_name = f"منشأة {row[search_column]}"
                            
                            st.subheader(f"🏢 {facility_name}")
                            
                            # عرض المعلومات في أعمدة
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.write("**المعلومات الأساسية:**")
                                # عرض الكود
                                if column_categories['codes']:
                                    code_col = column_categories['codes'][0]
                                    st.write(f"**الكود:** {row[code_col]}")
                                else:
                                    st.write(f"**المعرِّف:** {row[search_column]}")
                                
                                # عرض النوع إذا موجود
                                if column_categories['types']:
                                    type_col = column_categories['types'][0]
                                    st.write(f"**النوع:** {row[type_col]}")
                            
                            with col2:
                                st.write("**العنوان والموقع:**")
                                # عرض العنوان إذا موجود
                                if column_categories['addresses']:
                                    for addr_col in column_categories['addresses'][:2]:  # أول عمودين عنوان
                                        st.write(f"**{addr_col}:** {row[addr_col]}")
                                else:
                                    st.write("**العنوان:** غير متوفر")
                            
                            with col3:
                                st.write("**الحالة والإضافات:**")
                                # عرض الحالة إذا موجودة
                                if column_categories['statuses']:
                                    status_col = column_categories['statuses'][0]
                                    status_value = row[status_col]
                                    if any(word in str(status_value).lower() for word in ['مطابق', 'نعم', 'جيد']):
                                        st.markdown(f"**الحالة:** <span class='white-list-good'>مطابق</span>", unsafe_allow_html=True)
                                    elif any(word in str(status_value).lower() for word in ['غير', 'لا', 'رفض']):
                                        st.markdown(f"**الحالة:** <span class='white-list-bad'>غير مطابق</span>", unsafe_allow_html=True)
                                    else:
                                        st.markdown(f"**الحالة:** <span class='white-list-pending'>قيد المراجعة</span>", unsafe_allow_html=True)
                                else:
                                    st.write("**الحالة:** غير محددة")
                                
                                st.write("**حالة السجل:** نشط")
                            
                            # زر لتوسيع وعرض جميع البيانات
                            with st.expander("📋 عرض جميع البيانات"):
                                for col in data.columns:
                                    if pd.notna(row[col]) and str(row[col]).strip():
                                        st.write(f"**{col}:** {row[col]}")
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                            
            except Exception as e:
                st.error(f"❌ خطأ في البحث: {e}")

with tab2:
    st.header("📊 عرض البيانات الكاملة")
    
    if data.empty:
        st.error("❌ لا توجد بيانات متاحة للعرض")
    else:
        # عرض إحصائيات سريعة
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("إجمالي السجلات", len(data))
        with col2:
            st.metric("عدد الأعمدة", len(data.columns))
        with col3:
            non_empty = data.count()
            st.metric("أعلى عمود مملوء", f"{non_empty.max()}/{len(data)}")
        with col4:
            st.metric("أقل عمود مملوء", f"{non_empty.min()}/{len(data)}")
        
        # عرض تصنيف الأعمدة
        column_categories = classify_columns(data)
        
        st.subheader("📂 تصنيف الأعمدة")
        cat_cols = st.columns(5)
        
        with cat_cols[0]:
            st.write("**أكواد:**")
            for col in column_categories['codes'][:3]:
                st.code(col)
            if len(column_categories['codes']) > 3:
                st.write(f"و {len(column_categories['codes']) - 3} أكثر...")
        
        with cat_cols[1]:
            st.write("**أسماء:**")
            for col in column_categories['names'][:3]:
                st.code(col)
            if len(column_categories['names']) > 3:
                st.write(f"و {len(column_categories['names']) - 3} أكثر...")
        
        with cat_cols[2]:
            st.write("**عناوين:**")
            for col in column_categories['addresses'][:3]:
                st.code(col)
            if len(column_categories['addresses']) > 3:
                st.write(f"و {len(column_categories['addresses']) - 3} أكثر...")
        
        with cat_cols[3]:
            st.write("**حالات:**")
            for col in column_categories['statuses'][:3]:
                st.code(col)
            if len(column_categories['statuses']) > 3:
                st.write(f"و {len(column_categories['statuses']) - 3} أكثر...")
        
        with cat_cols[4]:
            st.write("**أخرى:**")
            for col in column_categories['other'][:3]:
                st.code(col)
            if len(column_categories['other']) > 3:
                st.write(f"و {len(column_categories['other']) - 3} أكثر...")
        
        # عرض البيانات الكاملة
        st.subheader("📋 البيانات الكاملة")
        st.dataframe(data, use_container_width=True)

with tab3:
    st.header("⚙️ الإعدادات والمساعدة")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🛠️ أدوات النظام")
        
        if st.button("🔄 تحديث البيانات"):
            st.cache_data.clear()
            st.rerun()
        
        if st.button("📥 تصدير البيانات"):
            csv = data.to_csv(index=False)
            st.download_button(
                label="📥 تحميل كملف CSV",
                data=csv,
                file_name="المنشآت_الغذائية.csv",
                mime="text/csv"
            )
    
    with col2:
        st.subheader("📊 إحصائيات")
        
        if not data.empty:
            st.write(f"**إجمالي السجلات:** {len(data)}")
            st.write(f"**عدد الأعمدة:** {len(data.columns)}")
            st.write(f"**تاريخ التحميل:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            # عرض أول 10 أعمدة
            st.write("**الأعمدة المتاحة:**")
            for col in data.columns[:10]:
                st.write(f"<span class='column-badge'>{col}</span>", unsafe_allow_html=True)
            if len(data.columns) > 10:
                st.write(f"و {len(data.columns) - 10} أعمدة أخرى...")
    
    st.subheader("📖 دليل الاستخدام")
    
    with st.expander("كيفية استخدام النظام"):
        st.write("""
        **🔍 البحث:**
        - اكتب أي كود أو اسم منشأة في مربع البحث
        - النظام سيبحث تلقائياً في أنسب عمود
        - يمكنك عرض جميع البيانات لكل منشأة
        
        **📊 عرض البيانات:**
        - شاهد إحصائيات البيانات الكاملة
        - اعرض تصنيف الأعمدة المختلفة
        - استعرض الجدول الكامل للبيانات
        
        **ملاحظة:** بما أن الأعمدة المتوقعة غير موجودة في البيانات الحالية، 
        يقوم النظام تلقائياً بتصنيف الأعمدة الموجودة ومحاولة التعرف عليها.
        """)

# تذييل الصفحة
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "© 2024 الهيئة القومية لسلامة الغذاء - نظام إدارة المنشآت الغذائية"
    "</div>",
    unsafe_allow_html=True
)
