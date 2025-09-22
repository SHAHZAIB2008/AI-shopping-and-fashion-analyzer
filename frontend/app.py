import streamlit as st
import requests
import io
import uuid
from PIL import Image
import json
import time

# Configuration
BACKEND_URL = "http://127.0.0.1:8000"

def reset_session():
    """Reset all session state variables"""
    st.session_state.image_analyzed = False
    st.session_state.image_analysis = ""
    st.session_state.current_image = None
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.chat_history = []
    st.session_state.fashion_items = []
    # Don't reset all_products to preserve previous searches
    if 'current_question' in st.session_state:
        del st.session_state.current_question

def analyze_image_function():
    """Handle image analysis"""
    with st.spinner("🤖 AI is analyzing your fashion image... This may take a few moments."):
        try:
            st.session_state.current_image.seek(0)
            files = {"file": (st.session_state.current_image.name, 
                            st.session_state.current_image.getvalue(), 
                            st.session_state.current_image.type)}
            
            start_time = time.time()
            response = requests.post(f"{BACKEND_URL}/analyze_image/", files=files)
            analysis_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    st.session_state.image_analysis = result.get("image_analysis", "")
                    st.session_state.fashion_items = result.get("fashion_items", [])
                    st.session_state.image_analyzed = True
                    
                    # Show success with timing
                    st.success(f"✅ Image analyzed successfully in {analysis_time:.1f} seconds!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Error: " + result.get("message", "Unknown error"))
            else:
                st.error(f"❌ Server error: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to backend. Make sure the FastAPI server is running on http://127.0.0.1:8000")
            st.info("💡 Run: `python -m uvicorn main:app --host 127.0.0.1 --port 8000`")
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")

def display_analysis_results():
    """Display the analysis results"""
    st.success("🎉 Analysis Complete!")
    
    # Show detected fashion items with enhanced styling
    if st.session_state.fashion_items:
        st.subheader("🏷️ Detected Fashion Items")
        items_html = ""
        for item in st.session_state.fashion_items:
            items_html += f'<span class="brand-badge">{item}</span> '
        st.markdown(items_html, unsafe_allow_html=True)
    
    # Show analysis in expandable section with better styling
    with st.expander("📋 View Complete AI Analysis", expanded=False):
        st.markdown(f'<div class="analysis-box">{st.session_state.image_analysis}</div>', 
                   unsafe_allow_html=True)

def handle_question_submission(question):
    """Handle question submission and product search"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("🔍 Processing your question...")
        progress_bar.progress(25)
        
        st.session_state.current_image.seek(0)
        files = {"file": (st.session_state.current_image.name, 
                        st.session_state.current_image.getvalue(), 
                        st.session_state.current_image.type)}
        data = {
            "question": question,
            "image_analysis": st.session_state.image_analysis
        }
        
        status_text.text("🤖 AI is thinking...")
        progress_bar.progress(50)
        
        start_time = time.time()
        response = requests.post(f"{BACKEND_URL}/ask_question/", files=files, data=data)
        
        status_text.text("🛍️ Searching for products...")
        progress_bar.progress(75)
        
        if response.status_code == 200:
            result = response.json()
            progress_bar.progress(100)
            status_text.text("✅ Complete!")
            
            if result.get("status") == "success":
                display_ai_response(result, question, time.time() - start_time)
            else:
                st.error("❌ Error: " + result.get("message", "Unknown error"))
        else:
            st.error(f"❌ Server error: {response.status_code}")
            
    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
    finally:
        progress_bar.empty()
        status_text.empty()

def display_ai_response(result, question, response_time):
    """Display AI response and add products to sidebar collection"""
    # Display AI Answer
    st.subheader("🤖 AI Fashion Assistant")
    
    # Create info box with question and timing
    info_col1, info_col2 = st.columns([3, 1])
    with info_col1:
        st.info(f"**Your Question:** {question}")
    with info_col2:
        st.metric("Response Time", f"{response_time:.1f}s")
    
    st.write(result.get("answer", ""))
    
    # Get products and add to sidebar collection
    products = result.get("products", [])
    total_products = result.get("total_products_found", len(products))
    
    if products:
        # Add products to the persistent collection
        if 'all_products' not in st.session_state:
            st.session_state.all_products = []
        
        # Add new products with metadata
        for product in products:
            product_entry = {
                **product,
                'question': question,
                'timestamp': time.time(),
                'category': result.get("category", ""),
                'search_session': st.session_state.session_id
            }
            st.session_state.all_products.append(product_entry)
        
        # Show confirmation in main area
        st.success(f"🎉 Found {len(products)} products! Check the sidebar to browse and shop.")
        
        # Show summary of new products found
        with st.expander(f"📋 Quick Preview - {len(products)} New Products", expanded=False):
            for i, product in enumerate(products[:3]):  # Show first 3 as preview
                st.write(f"**{i+1}.** {product.get('name', 'Product')} from {product.get('brand', 'Brand')} - {product.get('price', 'Price on request')}")
            if len(products) > 3:
                st.write(f"... and {len(products) - 3} more in the sidebar!")
    
    # Add to chat history
    st.session_state.chat_history.append({
        "question": question,
        "answer": result.get("answer", ""),
        "products": products,
        "category": result.get("category", ""),
        "total_products": total_products,
        "response_time": response_time
    })
    
    # Clear the question for next use
    st.session_state.current_question = ""

def display_question_interface():
    """Display the question interface"""
    st.markdown("---")
    st.subheader("💬 Ask Questions & Get Product Recommendations")
    
    # Enhanced question suggestions with better layout
    st.write("**🚀 Quick Questions:**")
    
    # Create a more organized suggestion layout
    suggestion_data = [
        ("👗 Give me a dress for my wedding", "Get bridal wear recommendations", "wedding_btn"),
        ("🎉 Show me party wear outfits", "Find party and event clothing", "party_btn"),
        ("👔 Find me formal office wear", "Professional clothing suggestions", "formal_btn"),
        ("🏠 Give me casual daily wear", "Comfortable everyday clothing", "casual_btn"),
        ("💰 What's the price range?", "Get pricing information", "price_btn"),
        ("🎨 Style and color advice", "Fashion styling tips", "style_btn"),
    ]
    
    cols = st.columns(3)
    for i, (question, help_text, key) in enumerate(suggestion_data):
        with cols[i % 3]:
            if st.button(question, key=key, help=help_text, use_container_width=True):
                st.session_state.current_question = question
    
    # Custom question input with better styling
    if 'current_question' not in st.session_state:
        st.session_state.current_question = ""
        
    question = st.text_area(
        "Or ask your own question:",
        value=st.session_state.current_question,
        placeholder="""Examples:
• Give me a dress for my wedding under PKR 30,000
• Show me casual kurtis from Khaadi
• Find party wear from Pakistani brands
• What accessories would match this outfit?
• Give me budget-friendly options""",
        height=120
    )
    
    # Enhanced ask button
    ask_col1, ask_col2 = st.columns([4, 1])
    with ask_col1:
        if st.button("🛍️ Get Fashion Recommendations", type="primary", use_container_width=True):
            if not question.strip():
                st.warning("⚠️ Please ask a question about the image.")
            else:
                handle_question_submission(question.strip())
    
    with ask_col2:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.current_question = ""
            st.rerun()

def display_welcome_section():
    """Display welcome section when no image is uploaded"""
    st.info("👆 Upload a fashion image to get started with AI analysis and personalized shopping recommendations!")
    
    # Enhanced demo section
    st.subheader("✨ What You Can Do:")
    
    demo_cols = st.columns(3)
    with demo_cols[0]:
        st.markdown("""
        <div class="feature-card">
            <h3>🔍 Analyze</h3>
            <p>Upload any fashion image and get detailed AI analysis of colors, styles, and clothing types</p>
        </div>
        """, unsafe_allow_html=True)
    
    with demo_cols[1]:
        st.markdown("""
        <div class="feature-card">
            <h3>💬 Ask</h3>
            <p>Ask specific questions like 'Give me a dress for my wedding' or 'Find casual wear under PKR 5000'</p>
        </div>
        """, unsafe_allow_html=True)
    
    with demo_cols[2]:
        st.markdown("""
        <div class="feature-card">
            <h3>🛍️ Shop</h3>
            <p>Get real product recommendations with images, prices and direct links to Pakistani fashion brands</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Sample images section
    st.subheader("📸 Try with Sample Images:")
    st.write("Don't have an image? Try these sample fashion images:")
    
    sample_cols = st.columns(4)
    sample_images = [
        ("https://assets0.mirraw.com/images/13171770/_0003_Layer_9_long_webp.webp?1743067196", "Traditional Dress"),
        ("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQDXQlxeoIRG5hkBVaTMYhayuSyzsSlD-mgVg&s", "Casual Wear"),
        ("https://jazmin.pk/cdn/shop/files/1_46e1a281-3085-41ba-bf23-1785e9c6069a.jpg?v=1733121391&width=1200", "Formal Wear")
    ]
    
    for i, (img_url, caption) in enumerate(sample_images):
        with sample_cols[i]:
            try:
                st.image(img_url, caption=caption, use_container_width=True)
            except:
                st.info(f"Sample: {caption}")
    
    # Reset state when no image (but preserve products)
    if st.session_state.image_analyzed:
        # Only reset image-related state, keep products
        st.session_state.image_analyzed = False
        st.session_state.image_analysis = ""
        st.session_state.current_image = None
        st.session_state.chat_history = []
        st.session_state.fashion_items = []

def display_sidebar_products():
    """Display all collected products in the sidebar with shopping functionality"""
    if 'all_products' not in st.session_state:
        st.session_state.all_products = []
    
    if st.session_state.all_products:
        total_products = len(st.session_state.all_products)
        
        # Header with stats
        st.markdown(f"""
        <div class="stats-card">
            <h3>🛍️ Your Shopping Collection</h3>
            <p><strong>{total_products}</strong> Products Found</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Filter and sort options
        st.markdown("**🔍 Filter Products:**")
        
        # Get unique brands and categories
        all_brands = list(set([p.get('brand', 'Unknown') for p in st.session_state.all_products]))
        all_categories = list(set([p.get('category', 'Uncategorized') for p in st.session_state.all_products]))
        
        # Filter controls
        filter_brand = st.selectbox("Brand:", ["All Brands"] + sorted(all_brands), key="sidebar_brand_filter")
        filter_category = st.selectbox("Category:", ["All Categories"] + sorted(all_categories), key="sidebar_category_filter")
        
        # Sort options
        sort_option = st.selectbox("Sort by:", [
            "Most Recent", 
            "Brand A-Z", 
            "Price (if available)",
            "By Question"
        ], key="sidebar_sort")
        
        # Apply filters
        filtered_products = st.session_state.all_products.copy()
        
        if filter_brand != "All Brands":
            filtered_products = [p for p in filtered_products if p.get('brand') == filter_brand]
        
        if filter_category != "All Categories":
            filtered_products = [p for p in filtered_products if p.get('category') == filter_category]
        
        # Apply sorting
        if sort_option == "Most Recent":
            filtered_products = sorted(filtered_products, key=lambda x: x.get('timestamp', 0), reverse=True)
        elif sort_option == "Brand A-Z":
            filtered_products = sorted(filtered_products, key=lambda x: x.get('brand', ''))
        elif sort_option == "By Question":
            filtered_products = sorted(filtered_products, key=lambda x: x.get('question', ''))
        
        st.markdown(f"**Showing {len(filtered_products)} of {total_products} products**")
        
        # Clear all products button
        if st.button("🗑️ Clear All Products", key="clear_all_products"):
            st.session_state.all_products = []
            st.rerun()
        
        # Display products
        for i, product in enumerate(filtered_products):
            with st.container():
                # Compact product card styling
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white; padding: 8px 10px; border-radius: 8px; margin: 6px 0;
                            box-shadow: 0 3px 5px rgba(0,0,0,0.07); font-size: 0.92em;">
                    <div style="display: flex; align-items: center;">
                        <div style="flex: 0 0 60px; margin-right: 10px;">
                            <img src="{product.get('image') or product.get('image_url', '')}" alt="img"
                                 style="width:60px;height:60px;object-fit:cover;border-radius:7px;border:1px solid #fff;">
                        </div>
                        <div style="flex: 1;">
                            <b>{product.get('name', 'Fashion Item')[:28]}{'...' if len(product.get('name', '')) > 28 else ''}</b>
                            <br>
                            <span style="font-size:0.85em;">{product.get('brand', 'Brand')}</span>
                            <br>
                            <span style="background: #ff8e53; color: white; border-radius: 10px; padding: 2px 8px; font-size:0.85em;">
                                {product.get('price', 'Price on request')}
                            </span>
                            <br>
                            <a href="{product.get('link', '#')}" target="_blank" style="color:#ffe082;font-size:0.85em;">🛒 Shop</a>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Show which question found this product
                if product.get('question'):
                    st.caption(f"📝 Found for: \"{product.get('question', '')[:30]}...\"")
                
                st.markdown("---")
        
        # Pagination for many products
        if len(filtered_products) > 10:
            st.info(f"💡 Showing first 10 products. Use filters to narrow down results.")
    
    else:
        st.info("🛍️ No products found yet. Upload an image and ask questions to start shopping!")
        
        # Show some tips
        st.markdown("""
        **💡 Tips to get started:**
        - Upload a fashion image
        - Ask specific questions like "Give me a dress for my wedding"
        - Browse products that match your style
        - Products will accumulate here for easy shopping
        """)

def display_chat_history():
    """Display chat history in a compact format"""
    if st.session_state.chat_history:
        total_conversations = len(st.session_state.chat_history)
        total_products = sum([len(chat.get('products', [])) for chat in st.session_state.chat_history])
        avg_response_time = sum([chat.get('response_time', 0) for chat in st.session_state.chat_history]) / total_conversations
        
        st.markdown(f"""
        <div class="stats-card">
            <h4>📊 Session Stats</h4>
            <p><strong>{total_conversations}</strong> Conversations</p>
            <p><strong>{total_products}</strong> Products Found</p>
            <p><strong>{avg_response_time:.1f}s</strong> Avg Response</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Compact chat history
        with st.expander("💬 View Chat History", expanded=False):
            for i, chat in enumerate(st.session_state.chat_history):
                st.markdown(f"""
                **Q{i+1}:** {chat['question'][:50]}{'...' if len(chat['question']) > 50 else ''}
                
                **A:** {chat['answer'][:100]}{'...' if len(chat['answer']) > 100 else ''}
                
                **Products:** {len(chat.get('products', []))} found | **Time:** {chat.get('response_time', 0):.1f}s
                
                ---
                """)

# Custom CSS for sidebar products
st.markdown("""
<style>
.sidebar-product-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 15px;
    border-radius: 10px;
    margin: 10px 0;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.product-header h4 {
    margin: 0 0 8px 0;
    font-size: 1em;
}

.brand-badge-small {
    background: linear-gradient(45deg, #4ecdc4, #44a08d);
    color: white;
    padding: 3px 8px;
    border-radius: 10px;
    font-size: 0.75em;
    font-weight: bold;
}

.sidebar-buy-button {
    background: linear-gradient(45deg, #ff6b6b, #feca57);
    border: none;
    color: white !important;
    padding: 8px 16px;
    border-radius: 20px;
    text-decoration: none;
    font-weight: bold;
    font-size: 0.9em;
    display: inline-block;
    margin: 8px 0;
    transition: all 0.3s ease;
    text-align: center;
    width: 100%;
}

.sidebar-buy-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    text-decoration: none;
    color: white !important;
}

.product-card {
    border: 1px solid #e1e5e9;
    border-radius: 15px;
    padding: 20px;
    margin: 15px 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.product-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.2);
}

.price-tag {
    background: linear-gradient(45deg, #ff6b6b, #ff8e53);
    color: white;
    padding: 8px 15px;
    border-radius: 25px;
    font-weight: bold;
    font-size: 1.1em;
    display: inline-block;
    margin: 8px 0;
    box-shadow: 0 4px 8px rgba(255, 107, 107, 0.3);
}

.brand-badge {
    background: linear-gradient(45deg, #4ecdc4, #44a08d);
    color: white;
    padding: 5px 12px;
    border-radius: 15px;
    font-size: 0.9em;
    font-weight: bold;
    display: inline-block;
    margin: 5px 5px 5px 0;
}

.buy-button {
    background: linear-gradient(45deg, #ff6b6b, #feca57);
    border: none;
    color: white;
    padding: 12px 24px;
    border-radius: 25px;
    text-decoration: none;
    font-weight: bold;
    font-size: 1em;
    display: inline-block;
    margin-top: 15px;
    transition: all 0.3s ease;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

.buy-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(0,0,0,0.3);
    text-decoration: none;
    color: white;
}

.stats-card {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
    padding: 15px;
    border-radius: 10px;
    margin: 10px 0;
    text-align: center;
}

.feature-card {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    color: white;
    padding: 20px;
    border-radius: 15px;
    margin: 10px;
    text-align: center;
}

.analysis-box {
    background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
    color: white;
    padding: 20px;
    border-radius: 15px;
    margin: 15px 0;
}
</style>
""", unsafe_allow_html=True)

# MAIN STREAMLIT APP STARTS HERE
st.set_page_config(
    page_title="AI Fashion Analyzer & Shopping Assistant",
    layout="wide",
    page_icon="👗"
)

st.title("👗 AI Fashion Analyzer & Shopping Assistant")
st.markdown("**Upload → Analyze → Ask → Shop** | Get personalized fashion recommendations with real product images from top Pakistani brands")

# Initialize session state
if 'image_analyzed' not in st.session_state:
    st.session_state.image_analyzed = False
if 'image_analysis' not in st.session_state:
    st.session_state.image_analysis = ""
if 'current_image' not in st.session_state:
    st.session_state.current_image = None
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'fashion_items' not in st.session_state:
    st.session_state.fashion_items = []
if 'all_products' not in st.session_state:
    st.session_state.all_products = []

# Create main layout with better proportions - sidebar is now wider for products
col1, col2 = st.columns([2.5, 1.5])

with col1:
    st.header("📷 Image Analysis & Shopping")
    
    # Enhanced image upload section
    uploaded_file = st.file_uploader(
        "Choose a fashion image to analyze", 
        type=["jpg", "jpeg", "png"],
        help="Upload clear images of clothing, outfits, or fashion items for AI analysis and shopping recommendations"
    )

    if uploaded_file:
        # Display image with enhanced formatting
        col_img, col_info = st.columns([2, 1])
        
        with col_img:
            st.image(uploaded_file, caption="Your Fashion Image", use_container_width=True)
        
        with col_info:
            st.markdown('<div class="analysis-box">', unsafe_allow_html=True)
            st.write("**📋 Image Details**")
            st.write(f"**Name:** {uploaded_file.name}")
            st.write(f"**Size:** {len(uploaded_file.getvalue()):,} bytes")
            st.write(f"**Format:** {uploaded_file.type}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Store the current image
        st.session_state.current_image = uploaded_file
        
        # Step 1: Analyze the image
        if not st.session_state.image_analyzed:
            analyze_col1, analyze_col2 = st.columns([3, 1])
            
            with analyze_col1:
                if st.button("🔍 Analyze Image with AI", type="primary", use_container_width=True):
                    analyze_image_function()
            
            with analyze_col2:
                st.info("💡 **Tip:** Clear, well-lit images work best!")
        
        # Step 2: Show analysis and questions
        if st.session_state.image_analyzed:
            display_analysis_results()
            display_question_interface()

    else:
        display_welcome_section()

# Enhanced Sidebar - Now focused on products and shopping
with col2:
    st.header("🛍️ Shopping Center")
    
    # Show current session info
    st.markdown(f"""
    <div style="background: linear-gradient(45deg, #667eea, #764ba2); color: white; padding: 10px; border-radius: 10px; margin: 10px 0;">
        <strong>🆔 Session:</strong><br>
        <code style="color: #fff;">{st.session_state.session_id[:8]}...</code>
    </div>
    """, unsafe_allow_html=True)
    
    # Display products (main focus of sidebar)
    display_sidebar_products()
    
    # Compact chat history
    st.markdown("---")
    display_chat_history()