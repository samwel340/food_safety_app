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
        # الرابط الجديد
        sheet_url = "https://docs.google.com/spreadsheets/d/1EN0muIIOrV5tqRoY02SX2Q5DdRFEM_CGo1Es4xueCgA/edit?usp=scv"
        data = pd.read_csv(sheet_url)
        
        # تنظيف أسماء الأعمدةcsv
        data.columns = data.columns.str.strip()
        
        return data
        
    except Exception as e:
        st.error(f"❌ خطأ في تحميل البيانات: {e}")
        return pd.DataFrame()

data = load_data()

# دالة للعثور على أفضل عمود للبحث
def find_best_search_column(data):
    """العثور على أفضل عمود للبحث بناءً على الأعمدة المتوقعة"""
    # البحث أولاً عن عمود "الكود المنشأة" كما طلب المستخدم
    if 'الكود المنشأة' in data.columns:
        return 'الكود المنشأة'
    
    possible_columns = [
        'الكود الجديد', 'الكود', 'كود', 'رقم', 'ID', 'Code', 'code',
        'كود المنشأة', 'رقم المنشأة', 'كود المنشأة'
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

# دالة لتصنيف الأعمدة بناءً على الأعمدة المطلوبة
def classify_columns(data):
    """تصنيف الأعمدة حسب نوعها مع التركيز على الأعمدة المطلوبة"""
    column_categories = {
        'codes': [],
        'names': [],
        'addresses': [],
        'types': [],
        'statuses': [],
        'dates': [],
        'other': []
    }
    
    # الكلمات المفتاحية باللغة العربية مع التركيز على الأعمدة المطلوبة
    name_keywords = ['اسم المنشأة بالبطاقة الضريبية', 'اسم المنشأة على اللافتة', 'اسم', 'name', 'Title', 'title', 'مسمى', 'شركة']
    code_keywords = ['الكود المنشأة', 'كود', 'code', 'رقم', 'id', 'ID', 'رمز']
    address_keywords = [
        'عنوان المنشأة (المحافظة)',
        'عنوان المنشأة (المنطقة / المدينة)',
        'عنوان المنشأة (تفصيلياً)',
        'عنوان', 'address', 'موقع', 'مكان', 'محافظة', 'مدينة', 'منطقة'
    ]
    type_keywords = ['فئة المنشأة', 'نوع', 'type', 'فئة', 'category', 'تصنيف']
    status_keywords = ['حالة', 'status', 'موقف', 'قائمة', 'بيضاء', 'نتيجة']
    date_keywords = ['تاريخ', 'date', 'وقت', 'time']
    
    # أعمدة يجب البحث عنها بشكل خاص
    specific_columns = {
        'فئة المنشأة': 'types',
        'اسم المنشأة بالبطاقة الضريبية': 'names',
        'اسم المنشأة على اللافتة': 'names',
        'عنوان المنشأة (المحافظة)': 'addresses',
        'عنوان المنشأة (المنطقة / المدينة)': 'addresses',
        'عنوان المنشأة (تفصيلياً)': 'addresses'
    }
    
    for col in data.columns:
        col_lower = col.lower()
        
        # التحقق من الأعمدة المحددة أولاً
        if col in specific_columns:
            column_categories[specific_columns[col]].append(col)
        elif any(keyword in col_lower for keyword in code_keywords):
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

# دالة للحصول على اسم المنشأة من الأعمدة المطلوبة
def get_facility_name(row, name_columns):
    """الحصول على اسم المنشأة من الأعمدة المحددة"""
    for col in ['اسم المنشأة بالبطاقة الضريبية', 'اسم المنشأة على اللافتة']:
        if col in row and pd.notna(row[col]) and str(row[col]).strip():
            return row[col]
    
    # إذا لم توجد الأعمدة المحددة، البحث في أي عمود أسماء
    for col in name_columns:
        if col in row and pd.notna(row[col]) and str(row[col]).strip():
            return row[col]
    
    return "منشأة غير معروفة"

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
        
        if search_column == 'الكود المنشأة':
            st.success("✅ تم العثور على عمود 'الكود المنشأة' وسيتم استخدامه للبحث")
        elif not column_categories['codes']:
            st.warning(f"⚠️ لم يتم العثور على عمود 'الكود المنشأة'. سيتم استخدام العمود: **{search_column}** للبحث")
        else:
            st.info(f"ℹ️ سيتم البحث في عمود: **{search_column}**")
        
        # عرض الأعمدة المطلوبة الموجودة
        required_columns = [
            'فئة المنشأة',
            'اسم المنشأة بالبطاقة الضريبية',
            'اسم المنشأة على اللافتة',
            'عنوان المنشأة (المحافظة)',
            'عنوان المنشأة (المنطقة / المدينة)',
            'عنوان المنشأة (تفصيلياً)'
        ]
        
        found_columns = [col for col in required_columns if col in data.columns]
        if found_columns:
            st.success(f"✅ تم العثور على {len(found_columns)} من الأعمدة المطلوبة")
        
        # مربع البحث
        st.markdown("""
            <div class="search-box">
                <h3>🔍 أدخل كود المنشأة للبحث</h3>
                <p>ابحث باستخدام كود المنشأة الموجود في عمود 'الكود المنشأة'</p>
            </div>
        """, unsafe_allow_html=True)
        
        search_term = st.text_input(
            f"بحث في عمود '{search_column}':",
            placeholder="أدخل كود المنشأة...",
            key="search_input"
        )
        
        if search_term:
            # البحث في العمود المحدد
            try:
                filtered_data = data[data[search_column].astype(str).str.contains(search_term, case=False, na=False)]
                
                if len(filtered_data) == 0:
                    st.warning("⚠️ لم يتم العثور على نتائج تطابق البحث")
                    
                    # اقتراح بحث في أعمدة أخرى
                    st.info("💡 جرب البحث في أعمدة أخرى:")
                    for col in data.columns[:5]:
                        if col != search_column:
                            sample = data[col].dropna().head(3).tolist()
                            sample_str = ", ".join([str(x) for x in sample[:2]])
                            if len(sample) > 2:
                                sample_str += "..."
                            st.write(f"- **{col}** (مثال: {sample_str})")
                else:
                    st.success(f"🎉 تم العثور على {len(filtered_data)} نتيجة")
                    
                    for idx, row in filtered_data.iterrows():
                        with st.container():
                            st.markdown('<div class="facility-card">', unsafe_allow_html=True)
                            
                            # الحصول على اسم المنشأة
                            facility_name = get_facility_name(row, column_categories['names'])
                            
                            # عرض الكود أولاً
                            code_value = "غير محدد"
                            if search_column in row:
                                code_value = row[search_column]
                            
                            st.subheader(f"🏢 {facility_name}")
                            st.write(f"**الكود:** {code_value}")
                            
                            # عرض المعلومات في أعمدة
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.write("**فئة المنشأة:**")
                                if 'فئة المنشأة' in row and pd.notna(row['فئة المنشأة']):
                                    st.write(f"**{row['فئة المنشأة']}**")
                                else:
                                    st.write("غير محدد")
                                
                                st.write("**أسماء المنشأة:**")
                                name_fields = []
                                if 'اسم المنشأة بالبطاقة الضريبية' in row and pd.notna(row['اسم المنشأة بالبطاقة الضريبية']):
                                    name_fields.append(f"الضريبي: {row['اسم المنشأة بالبطاقة الضريبية']}")
                                if 'اسم المنشأة على اللافتة' in row and pd.notna(row['اسم المنشأة على اللافتة']):
                                    name_fields.append(f"اللافتة: {row['اسم المنشأة على اللافتة']}")
                                
                                if name_fields:
                                    for name_field in name_fields:
                                        st.write(f"• {name_field}")
                                else:
                                    st.write("غير متوفر")
                            
                            with col2:
                                st.write("**العنوان:**")
                                address_parts = []
                                
                                if 'عنوان المنشأة (المحافظة)' in row and pd.notna(row['عنوان المنشأة (المحافظة)']):
                                    address_parts.append(f"**المحافظة:** {row['عنوان المنشأة (المحافظة)']}")
                                
                                if 'عنوان المنشأة (المنطقة / المدينة)' in row and pd.notna(row['عنوان المنشأة (المنطقة / المدينة)']):
                                    address_parts.append(f"**المنطقة/المدينة:** {row['عنوان المنشأة (المنطقة / المدينة)']}")
                                
                                if 'عنوان المنشأة (تفصيلياً)' in row and pd.notna(row['عنوان المنشأة (تفصيلياً)']):
                                    address_parts.append(f"**التفاصيل:** {row['عنوان المنشأة (تفصيلياً)']}")
                                
                                if address_parts:
                                    for part in address_parts:
                                        st.write(part)
                                else:
                                    # البحث في أي عمود عناوين آخر
                                    for addr_col in column_categories['addresses'][:2]:
                                        if addr_col in row and pd.notna(row[addr_col]):
                                            st.write(f"**{addr_col}:** {row[addr_col]}")
                                    if len(column_categories['addresses']) == 0:
                                        st.write("غير متوفر")
                            
                            with col3:
                                st.write("**الحالة والإضافات:**")
                                # عرض الحالة إذا موجودة
                                if column_categories['statuses']:
                                    status_col = column_categories['statuses'][0]
                                    if status_col in row:
                                        status_value = row[status_col]
                                        if any(word in str(status_value).lower() for word in ['مطابق', 'نعم', 'جيد', 'موافق']):
                                            st.markdown(f"**الحالة:** <span class='white-list-good'>مطابق</span>", unsafe_allow_html=True)
                                        elif any(word in str(status_value).lower() for word in ['غير', 'لا', 'رفض', 'مخالف']):
                                            st.markdown(f"**الحالة:** <span class='white-list-bad'>غير مطابق</span>", unsafe_allow_html=True)
                                        else:
                                            st.markdown(f"**الحالة:** <span class='white-list-pending'>قيد المراجعة</span>", unsafe_allow_html=True)
                                else:
                                    st.write("**الحالة:** غير محددة")
                                
                                st.write("**حالة السجل:** نشط")
                            
                            # زر لتوسيع وعرض جميع البيانات
                            with st.expander("📋 عرض جميع بيانات المنشأة"):
                                st.write("**جميع البيانات:**")
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
        
        # عرض الأعمدة المطلوبة
        st.subheader("🎯 الأعمدة المطلوبة")
        required_columns = [
            'فئة المنشأة',
            'اسم المنشأة بالبطاقة الضريبية',
            'اسم المنشأة على اللافتة',
            'عنوان المنشأة (المحافظة)',
            'عنوان المنشأة (المنطقة / المدينة)',
            'عنوان المنشأة (تفصيلياً)'
        ]
        
        req_cols = st.columns(3)
        col_idx = 0
        
        for col in required_columns:
            with req_cols[col_idx % 3]:
                if col in data.columns:
                    st.success(f"✅ {col}")
                    non_null = data[col].count()
                    st.caption(f"({non_null}/{len(data)} سجل)")
                else:
                    st.error(f"❌ {col}")
            col_idx += 1
        
        # عرض تصنيف الأعمدة
        column_categories = classify_columns(data)
        
        st.subheader("📂 تصنيف الأعمدة")
        cat_cols = st.columns(5)
        
        categories = [
            ('أكواد', column_categories['codes']),
            ('أسماء', column_categories['names']),
            ('عناوين', column_categories['addresses']),
            ('أنواع', column_categories['types']),
            ('أخرى', column_categories['other'])
        ]
        
        for idx, (cat_name, cat_columns) in enumerate(categories):
            with cat_cols[idx]:
                st.write(f"**{cat_name}:**")
                for col in cat_columns[:5]:
                    st.code(col, language=None)
                if len(cat_columns) > 5:
                    st.write(f"و {len(cat_columns) - 5} أكثر...")
        
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
            csv = data.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 تحميل كملف CSV",
                data=csv,
                file_name="المنشآت_الغذائية.csv",
                mime="text/csv"
            )
        
        # عرض أعمدة البحث المتاحة
        st.subheader("🔍 أعمدة البحث المتاحة")
        search_column = find_best_search_column(data)
        st.write(f"**عمود البحث الحالي:** {search_column}")
        
        # اختيار عمود بحث يدوي
        if len(data.columns) > 0:
            selected_col = st.selectbox(
                "اختر عمود بحث آخر:",
                data.columns,
                index=list(data.columns).index(search_column) if search_column in data.columns else 0
            )
            if selected_col != search_column:
                st.info(f"يمكنك استخدام عمود **{selected_col}** للبحث")
    
    with col2:
        st.subheader("📊 إحصائيات")
        
        if not data.empty:
            st.write(f"**إجمالي السجلات:** {len(data)}")
            st.write(f"**عدد الأعمدة:** {len(data.columns)}")
            st.write(f"**تاريخ التحميل:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            # معلومات عن الأعمدة المطلوبة
            st.write("**الأعمدة المطلوبة:**")
            required_columns = [
                'فئة المنشأة',
                'اسم المنشأة بالبطاقة الضريبية',
                'اسم المنشأة على اللافتة',
                'عنوان المنشأة (المحافظة)',
                'عنوان المنشأة (المنطقة / المدينة)',
                'عنوان المنشأة (تفصيلياً)'
            ]
            
            for col in required_columns[:5]:
                if col in data.columns:
                    st.success(f"✅ {col}")
                else:
                    st.error(f"❌ {col}")
            if len(required_columns) > 5:
                st.write(f"و {len(required_columns) - 5} أعمدة أخرى...")
    
    st.subheader("📖 دليل الاستخدام")
    
    with st.expander("كيفية استخدام النظام"):
        st.write("""
        **🔍 البحث:**
        1. انتقل إلى تبويب "البحث"
        2. أدخل كود المنشأة في مربع البحث (البحث في عمود "الكود المنشأة")
        3. سيظهر لك جميع المنشآت التي تطابق البحث
        4. يمكنك عرض تفاصيل كل منشأة بالكامل
        
        **📊 عرض البيانات:**
        - شاهد إحصائيات البيانات الكاملة
        - اعرض تصنيف الأعمدة المختلفة
        - استعرض الجدول الكامل للبيانات
        - تحقق من وجود الأعمدة المطلوبة
        
        **🎯 الأعمدة المطلوبة التي يتم عرضها:**
        - فئة المنشأة
        - اسم المنشأة بالبطاقة الضريبية
        - اسم المنشأة على اللافتة
        - عنوان المنشأة (المحافظة)
        - عنوان المنشأة (المنطقة / المدينة)
        - عنوان المنشأة (تفصيلياً)
        
        **ملاحظة:** إذا لم تكن الأعمدة المطلوبة موجودة بنفس الأسماء، 
        سيقوم النظام بمحاولة التعرف على الأعمدة المشابهة تلقائياً.
        """)

# تذييل الصفحة
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "© 2024 الهيئة القومية لسلامة الغذاء - نظام إدارة المنشآت الغذائية"
    "</div>",
    unsafe_allow_html=True
)
