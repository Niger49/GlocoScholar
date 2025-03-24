import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import pandas as pd
# from GlucoScholar import randomForest, ImageProcessor, InformationFetcher
from test_main import randomForest, ImageProcessor, InformationFetcher
import matplotlib.pyplot as plt
import webbrowser
import time
from tkinter import scrolledtext
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import sqlite3
from datetime import datetime
from tkcalendar import DateEntry 
import csv



class DiabetesPredictorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GlucoScholar Diabetes Predictor")
        self.root.geometry("1200x650")
        
        
        # Configure default font and colors
        self.root.configure(bg='#f0f0f0')
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Set default font
        self.root.option_add('*Font', 'Arial 12')
        
        # Configure style for notebook tabs
        self.style.configure('TNotebook', background='#f0f0f0')
        self.style.configure('TNotebook.Tab', 
                           font=('Arial', 12, 'bold'),
                           padding=[20, 6],
                           background='#d9d9d9',
                           foreground='#2c3e50')
        self.style.map('TNotebook.Tab',
                      background=[('selected', '#3498db')],
                      foreground=[('selected', '#ffffff')])
        
        # Initialize components
        self.radFor = randomForest()
        self.image_processor = ImageProcessor()
        self.info_fetcher = InformationFetcher()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True)
        
        # Create frames with consistent styling
        self._create_frames()
        
        # Initialize components for each tab
        self.create_dataset_tab()
        self.create_image_tab()
        self.create_predict_tab()
        self.create_medical_tab()
        self.create_report_tab() 
        
        # Database initialization
        self.conn = sqlite3.connect('diabetes_predictions.db')
        self.create_prediction_table()
        
        # Add this to handle database closure on exit
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # for custom csv file generation using a particular time period
        # self.create_dataset_tab()
        # self.create_image_tab()
        # self.create_predict_tab()
        # self.create_medical_tab()
        # self.create_report_tab() 
    
    def create_prediction_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS predictions
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                        gender TEXT,
                        age REAL,
                        hypertension INTEGER,
                        heart_disease INTEGER,
                        smoking_history TEXT,
                        bmi REAL,
                        HbA1c_level REAL,
                        blood_glucose_level REAL,
                        prediction_result TEXT,
                        timestamp DATETIME)''')
        self.conn.commit()

    def on_close(self):
        """Handle database connection closure when app exits"""
        self.conn.close()
        self.root.destroy()
        
    def save_prediction(self, input_data, prediction_result):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''INSERT INTO predictions 
                            (gender, age, hypertension, heart_disease, smoking_history,
                            bmi, HbA1c_level, blood_glucose_level, prediction_result, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (input_data['gender'],
                            input_data['age'],
                            input_data['hypertension'],
                            input_data['heart_disease'],
                            input_data['smoking_history'],
                            input_data['bmi'],
                            input_data['HbA1c_level'],
                            input_data['blood_glucose_level'],
                            prediction_result,
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            self.conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to save prediction: {str(e)}")

        
    def _create_frames(self):
        # Create and style frames
        self.dataset_frame = ttk.Frame(self.notebook, style='Custom.TFrame')
        self.image_frame = ttk.Frame(self.notebook, style='Custom.TFrame')
        self.predict_frame = ttk.Frame(self.notebook, style='Custom.TFrame')
        
        self.notebook.add(self.dataset_frame, text='Dataset Analysis')
        self.notebook.add(self.image_frame, text='Image Analysis')
        self.notebook.add(self.predict_frame, text='Diabetes Prediction')
        
        # Configure frame style
        self.style.configure('Custom.TFrame', background='#ffffff', borderwidth=2, relief='groove')
        
        self.medical_frame = ttk.Frame(self.notebook, style='Custom.TFrame')
        self.notebook.add(self.medical_frame, text='Medical Support')
        
        self.report_frame = ttk.Frame(self.notebook, style='Custom.TFrame')
        # self.notebook.add(self.report_frame, text='Generate Reports')

        
    
    def create_dataset_tab(self):
        # Dataset upload section
        ttk.Label(self.dataset_frame, text="Upload Dataset:", background='#ffffff').grid(row=0, column=0, padx=10, pady=10)
        self.dataset_path = tk.StringVar()
        entry = ttk.Entry(self.dataset_frame, textvariable=self.dataset_path, width=50)
        entry.grid(row=0, column=1, padx=10)
        ttk.Button(self.dataset_frame, text="Browse", command=self.load_dataset).grid(row=0, column=2)
        
        # Style for text widget
        self.results_text = tk.Text(self.dataset_frame, height=9, width=60, 
                                  bg='#ffffff', fg='#2c3e50',
                                  font=('Arial', 11))
        self.results_text.grid(row=1, column=0, columnspan=3, padx=10, pady=5)
    
    
    def create_report_tab(self):
        # Create new tab for reports
        self.report_frame = ttk.Frame(self.notebook, style='Custom.TFrame')
        self.notebook.add(self.report_frame, text='Generate Reports')
        
        # Date selection
        ttk.Label(self.report_frame, text="Start Date:", background='#ffffff').grid(row=0, column=0, padx=10, pady=10)
        self.start_date = DateEntry(self.report_frame)
        self.start_date.grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(self.report_frame, text="End Date:", background='#ffffff').grid(row=1, column=0, padx=10, pady=10)
        self.end_date = DateEntry(self.report_frame)
        self.end_date.grid(row=1, column=1, padx=10, pady=10)
        
        # Generate report button
        ttk.Button(self.report_frame, 
                text="Generate CSV Report", 
                command=self.generate_csv_report,
                style='Accent.TButton').grid(row=2, column=0, columnspan=2, pady=10)
        
        # Status label
        self.report_status = ttk.Label(self.report_frame, text="", foreground='green')
        self.report_status.grid(row=3, column=0, columnspan=2)

        
    def create_image_tab(self):
        # Image upload section
        ttk.Label(self.image_frame, text="Upload Image:", background='#ffffff').grid(row=0, column=0, padx=10, pady=10)
        self.image_path = tk.StringVar()
        ttk.Entry(self.image_frame, textvariable=self.image_path, width=50).grid(row=0, column=1, padx=10)
        ttk.Button(self.image_frame, text="Browse", command=self.load_image).grid(row=0, column=2)
        
        # Style buttons
        self.style.configure('TButton', padding=6, relief='flat', background='#3498db', foreground='white')
        ttk.Button(self.image_frame, text="Extract Text", command=self.process_image).grid(row=1, column=0, pady=10)
        ttk.Button(self.image_frame, text="Search Online", command=self.search_online).grid(row=1, column=1, pady=10)
        
        # Configure scrolled text
        self.image_text = scrolledtext.ScrolledText(self.image_frame, height=30, width=80,

                                                  wrap=tk.WORD, bg='#ffffff', fg='#2c3e50',
                                                  font=('Arial', 11))
        self.image_text.grid(row=2, column=0, columnspan=3, padx=10, pady=10)
        
        # Hyperlink styling
        self.image_text.tag_configure("hyperlink", foreground='#3498db', underline=1)
        self.image_text.tag_bind("hyperlink", "<Button-1>", self._open_url)
        self.image_text.tag_bind("hyperlink", "<Enter>", lambda e: self.image_text.config(cursor="hand2"))
        self.image_text.tag_bind("hyperlink", "<Leave>", lambda e: self.image_text.config(cursor=""))
    
    def _open_url(self, event):
        # Get the index of the mouse click
        index = self.image_text.index(f"@{event.x},{event.y}")
        # Get the tags at this index
        tags = self.image_text.tag_names(index)
        # Find the URL associated with this position
        for tag in tags:
            if tag.startswith("url-"):
                url = tag[4:]  # Remove 'url-' prefix
                webbrowser.open_new_tab(url)
                break
       
    
    # def search_online(self):
    #     query = self.image_text.get("1.0", "end-1c").split('\n')[-1]
    #     if query:
    #         try:
    #             # Show searching status
    #             self.image_text.insert(tk.END, "\n\nSearching...\n")
    #             self.root.update()  # Update UI to show status
                
    #             # Add delay before search
    #             time.sleep(2)  # 2-second delay
                
    #             results = self.info_fetcher.google_search(query)
                
    #             # Remove "Searching..." text
    #             self.image_text.delete("end-2c linestart", "end-1c lineend")
                
    #             if results:
    #                 self.image_text.insert(tk.END, "\nSearch Results:\n")
    #                 # Insert each URL as a clickable link
    #                 for i, url in enumerate(results[:3], 1):
    #                     self.image_text.insert(tk.END, f"{i}. ", "normal")
    #                     self.image_text.insert(tk.END, url + "\n", f"hyperlink url-{url}")
    #             else:
    #                 self.image_text.insert(tk.END, "\nNo results found or rate limit reached. Please try again later.\n")
                    
    #         except Exception as e:
    #             if "429" in str(e):
    #                 messagebox.showwarning(
    #                     "Rate Limit", 
    #                     "Search rate limit reached. Please wait a few minutes before trying again."
    #                 )
    #             else:
    #                 messagebox.showerror("Error", f"Search failed: {str(e)}")
    
    # def search_online(self):
    #     # Get full text content without splitting
    #     query = self.image_text.get("1.0", "end-1c").strip()
    #     print(query)
        
    #     if query:
    #         try:
    #             # Show searching status
    #             self.image_text.insert(tk.END, "\n\nSearching...\n")
    #             self.root.update()

    #             # Add initial delay
    #             time.sleep(2)

    #             # Get full set of results
    #             results = self.info_fetcher.google_search(query)
                
    #             # Clear searching status
    #             self.image_text.delete("end-2c linestart", "end-1c lineend")
                
    #             print(results)
    #             print(len(results))
                
    #             if results and len(results) > 0:
    #                 self.image_text.insert(tk.END, "\nSearch Results:\n")
    #                 # Make sure we get all results (up to 3)
    #                 for i, url in enumerate(results[:3], 1):
    #                     self.image_text.insert(tk.END, f"{i}. ", "normal")
    #                     self.image_text.insert(tk.END, url + "\n", f"hyperlink url-{url}")
    #                     time.sleep(0.5)  # Small delay between displaying results
    #             else:
    #                 self.image_text.insert(tk.END, "\nSupporting medical documentation:\n")
    #                 default_urls = [
    #                     "https://www.diabetes.org/",
    #                     "https://www.niddk.nih.gov/health-information/diabetes",
    #                     "https://www.who.int/health-topics/diabetes"
    #                 ]
    #                 for i, url in enumerate(default_urls, 1):
    #                     self.image_text.insert(tk.END, f"{i}. ", "normal")
    #                     self.image_text.insert(tk.END, url + "\n", f"hyperlink url-{url}")

    #         except Exception as e:
    #             if "429" in str(e):
    #                 self.image_text.insert(tk.END, "\nSearch rate limit reached. Using alternative resources:\n")
    #                 default_urls = [
    #                     "https://www.diabetes.org/",
    #                     "https://www.niddk.nih.gov/health-information/diabetes",
    #                     "https://www.who.int/health-topics/diabetes"
    #                 ]
    #                 for i, url in enumerate(default_urls, 1):
    #                     self.image_text.insert(tk.END, f"{i}. ", "normal")
    #                     self.image_text.insert(tk.END, url + "\n", f"hyperlink url-{url}")
    #             else:
    #                 messagebox.showerror("Error", f"Search failed: {str(e)}")
    
                
    def create_predict_tab(self):
        # Style input fields
        self.style.configure('TEntry', padding=5, relief='flat', background='#ffffff')
        
        fields = [
            ('gender', 'Gender (Male/Female/Other):'),
            ('age', 'Age:'),
            ('hypertension', 'Hypertension (0/1):'),
            ('heart_disease', 'Heart Disease (0/1):'),
            ('smoking_history', 'Smoking History(never/former/current/No Info/ever/not current):'),
            ('bmi', 'BMI:'),
            ('HbA1c_level', 'HbA1c Level:'),
            ('blood_glucose_level', 'Blood Glucose Level:')
        ]
        
        self.entries = {}
        for i, (field, label) in enumerate(fields):
            ttk.Label(self.predict_frame, text=label, background='#ffffff').grid(row=i, column=0, padx=10, pady=5, sticky='w')
            self.entries[field] = ttk.Entry(self.predict_frame)
            self.entries[field].grid(row=i, column=1, padx=10, pady=5)
        
        # Prediction button styling
        self.style.configure('Accent.TButton', background='#27ae60', foreground='white')
        # Create custom style for the prediction button
        style = ttk.Style()
        style.configure('Predict.TButton', 
                    font=('Arial', 14, 'bold'),
                    padding=10)

        # Prediction button and result with custom style
        ttk.Button(self.predict_frame, 
                text="Predict Diabetes", 
                command=self.predict_diabetes,
                style='Predict.TButton').grid(row=8, column=0, columnspan=2, pady=10)
        
        self.result_label = ttk.Label(self.predict_frame, text="", font=('Arial', 16))
        self.result_label.grid(row=9, column=0, columnspan=2, pady=10)
        
    def create_medical_tab(self):
        # Medical advice display
        self.advice_text = scrolledtext.ScrolledText(self.medical_frame, 
                                                height=15, width=80,
                                                wrap=tk.WORD, 
                                                bg='#ffffff', fg='#2c3e50',
                                                font=('Arial', 11))
        self.advice_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # PDF generation button
        ttk.Button(self.predict_frame, 
                text="Generate PDF Report", 
                command=self.generate_pdf_report,
                style='Accent.TButton').grid(row=10, column=0, columnspan=2, pady=10)
    

    def load_dataset(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            self.dataset_path.set(file_path)
            try:
                # Read the dataset
                df = pd.read_csv(file_path)
                
                # Ensure all required columns are present
                required_columns = [
                    'gender', 'age', 'hypertension', 'heart_disease',
                    'smoking_history', 'bmi', 'HbA1c_level', 'blood_glucose_level'
                ]
                
                # Check if all required columns exist
                missing_cols = [col for col in required_columns if col not in df.columns]
                if missing_cols:
                    raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")
                
                # Handle unknown categories for gender
                known_genders = self.radFor.gender_encoder.classes_
                df['gender'] = df['gender'].apply(
                    lambda x: x if x in known_genders else known_genders[0]
                )
                
                # Handle unknown categories for smoking_history
                known_smoking = self.radFor.smoking_history_encoder.classes_
                df['smoking_history'] = df['smoking_history'].apply(
                    lambda x: x if x in known_smoking else known_smoking[0]
                )
                
                # Encode categorical variables
                df['gender'] = self.radFor.gender_encoder.transform(df['gender'])
                df['smoking_history'] = self.radFor.smoking_history_encoder.transform(df['smoking_history'])
                
                # Reorder columns to match training data order
                df = df[required_columns]
                
                # Make predictions
                predictions = self.radFor.model.predict(df)
                diabetic = sum(predictions)
                non_diabetic = len(predictions) - diabetic
                
                 # Display results
                self.results_text.delete(1.0, tk.END)
                self.results_text.insert(tk.END, f"Dataset: {os.path.basename(file_path)}\n")
                self.results_text.insert(tk.END, f"Total Cases: {len(predictions)}\n")
                self.results_text.insert(tk.END, f"Diabetic Cases: {diabetic}\n")
                self.results_text.insert(tk.END, f"Non-Diabetic Cases: {non_diabetic}\n")
                self.results_text.insert(tk.END, f"Diabetic Percentage: {(diabetic/len(predictions))*100:.2f}%\n\n")
                
                # Create pie chart
                fig, ax = plt.subplots(figsize=(5, 4))
                labels = ['Diabetic', 'Non-Diabetic']
                sizes = [diabetic, non_diabetic]
                colors = ['#ff9999', '#66b3ff']
                
                ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                    startangle=90, shadow=True)
                ax.axis('equal')
                plt.title('Diabetes Prediction Distribution')
                
                # Embed the plot in tkinter
                from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
                if hasattr(self, 'canvas'):
                    self.canvas.get_tk_widget().destroy()
                self.canvas = FigureCanvasTkAgg(fig, master=self.dataset_frame)
                self.canvas.draw()
                self.canvas.get_tk_widget().grid(row=2, column=0, columnspan=3, padx=10, pady=10)
                
                # Add warning if unknown categories were found
                if df['gender'].isin([known_genders[0]]).any() or df['smoking_history'].isin([known_smoking[0]]).any():
                    warning_msg = "Note: Some records contained unknown categories and were mapped to default values."
                    self.results_text.insert(tk.END, warning_msg)
                    
            except ValueError as ve:
                messagebox.showerror("Error", str(ve))
            except Exception as e:
                messagebox.showerror("Error", f"Error processing dataset: {str(e)}")
                
    def load_image(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.image_path.set(file_path)
            
    def process_image(self):
        if self.image_path.get():
            try:
                extracted_text = self.image_processor.extract_text(self.image_path.get())
                self.image_text.delete(1.0, tk.END)
                self.image_text.insert(tk.END, "Extracted Text:\n" + extracted_text)
                print("Extracted Text: ", self.image_text.get("1.0", "end-1c"))
            except Exception as e:
                messagebox.showerror("Error", f"Error processing image: {str(e)}")
                
    # def search_online(self):
    #     query = self.image_text.get("1.0", "end-1c")
    #     print("🔖 Text for search: ", query)
    #     if query:
    #         try:
    #             # Show searching status
    #             self.image_text.insert(tk.END, "\n\nSearching...\n")
    #             self.root.update()

    #             # Add initial delay
    #             time.sleep(2)

    #             results = self.info_fetcher.google_search(query=query)
                
    #             # Clear searching status
    #             self.image_text.delete("end-2c linestart", "end-1c lineend")
                
    #             if results:
    #                 self.image_text.insert(tk.END, "\nSearch Results:\n")
    #                 for i, url in enumerate(results, 1):
    #                     self.image_text.insert(tk.END, f"{i}. ", "normal")
    #                     self.image_text.insert(tk.END, url + "\n", f"hyperlink url-{url}")
    #             else:
    #                 self.image_text.insert(tk.END, "\nUsing alternative medical resources:\n")
    #                 default_urls = [
    #                     "https://www.diabetes.org/",
    #                     "https://www.niddk.nih.gov/health-information/diabetes",
    #                     "https://www.who.int/health-topics/diabetes"
    #                 ]
    #                 for i, url in enumerate(default_urls, 1):
    #                     self.image_text.insert(tk.END, f"{i}. ", "normal")
    #                     self.image_text.insert(tk.END, url + "\n", f"hyperlink url-{url}")

    #         except Exception as e:
    #             if "429" in str(e):
    #                 self.image_text.insert(tk.END, "\nUsing alternative medical resources:\n")
    #                 default_urls = [
    #                     "https://www.diabetes.org/",
    #                     "https://www.niddk.nih.gov/health-information/diabetes",
    #                     "https://www.who.int/health-topics/diabetes"
    #                 ]
    #                 for i, url in enumerate(default_urls, 1):
    #                     self.image_text.insert(tk.END, f"{i}. ", "normal")
    #                     self.image_text.insert(tk.END, url + "\n", f"hyperlink url-{url}")
    #             else:
    #                 messagebox.showerror("Error", f"Search failed: {str(e)}")
    
    def search_online(self):
        query = self.image_text.get("1.0", "end-1c")
        print("🔖 Text for search: ", query)
        if query:
            try:
                # Show searching status
                self.image_text.insert(tk.END, "\n\nSearching...\n")
                self.root.update()

                # Add initial delay
                time.sleep(2)

                results = self.info_fetcher.google_search(query)
                
                # Clear searching status
                self.image_text.delete("end-2c linestart", "end-1c lineend")
                
                if results:
                    self.image_text.insert(tk.END, "\nSearch Results:\n")
                    for i, url in enumerate(results[:5], 1):
                        # Enhanced URL validation and completion
                        if not url.startswith(('http://', 'https://')):
                            url = f"https://{url}"
                        if 'google.com' in url:
                            continue  # Skip Google links entirely
                        self.image_text.insert(tk.END, f"{i}. ", "normal")
                        self.image_text.insert(tk.END, url + "\n", f"hyperlink url-{url}")

                else:
                    self.image_text.insert(tk.END, "\nUsing alternative medical resources:\n")
                    default_urls = [
                        "https://www.diabetes.org/",
                        "https://www.niddk.nih.gov/health-information/diabetes",
                        "https://www.who.int/health-topics/diabetes"
                    ]
                    for i, url in enumerate(default_urls, 1):
                        self.image_text.insert(tk.END, f"{i}. ", "normal")
                        self.image_text.insert(tk.END, url + "\n", f"hyperlink url-{url}")

            except Exception as e:
                if "429" in str(e):
                    self.image_text.insert(tk.END, "\nUsing alternative medical resources:\n")
                    default_urls = [
                        "https://www.diabetes.org/",
                        "https://www.niddk.nih.gov/health-information/diabetes",
                        "https://www.who.int/health-topics/diabetes"
                    ]
                    for i, url in enumerate(default_urls, 1):
                        self.image_text.insert(tk.END, f"{i}. ", "normal")
                        self.image_text.insert(tk.END, url + "\n", f"hyperlink url-{url}")
                else:
                    messagebox.showerror("Error", f"Search failed: {str(e)}")
                
    def predict_diabetes(self):
        try:
            input_data = {
                'gender': self.entries['gender'].get(),
                'age': float(self.entries['age'].get()),
                'hypertension': int(self.entries['hypertension'].get()),
                'heart_disease': int(self.entries['heart_disease'].get()),
                'smoking_history': self.entries['smoking_history'].get(),
                'bmi': float(self.entries['bmi'].get()),
                'HbA1c_level': float(self.entries['HbA1c_level'].get()),
                'blood_glucose_level': float(self.entries['blood_glucose_level'].get())
            }
            
            # Handle unknown categories
            if input_data['gender'] not in self.radFor.gender_encoder.classes_:
                input_data['gender'] = self.radFor.gender_encoder.classes_[0]
                messagebox.showwarning("Warning", f"Unknown gender category. Using default: {input_data['gender']}")
                
            if input_data['smoking_history'] not in self.radFor.smoking_history_encoder.classes_:
                input_data['smoking_history'] = self.radFor.smoking_history_encoder.classes_[0]
                messagebox.showwarning("Warning", f"Unknown smoking history category. Using default: {input_data['smoking_history']}")
            
            # Convert to DataFrame for prediction
            df = pd.DataFrame([input_data])
            
            # Encode categorical variables
            df['gender'] = self.radFor.gender_encoder.transform(df['gender'])
            df['smoking_history'] = self.radFor.smoking_history_encoder.transform(df['smoking_history'])
            
            prediction = self.radFor.model.predict(df)
            result = "Diabetic" if prediction[0] == 1 else "Not Diabetic"
            self.result_label.config(text=f"Prediction Result: {result}", foreground='red' if prediction[0] else 'green')
            
            prediction = self.radFor.model.predict(df)
            result = "Diabetic" if prediction[0] == 1 else "Not Diabetic"
            self.result_label.config(text=f"Prediction Result: {result}", 
                                foreground='red' if prediction[0] else 'green')
            
            # Save to database
            self.save_prediction(input_data, result)
            
            
            # Update medical recommendations
            self.advice_text.delete(1.0, tk.END)
            recommendations = self.get_medical_recommendations(prediction[0], input_data)
            self.advice_text.insert(tk.END, "Personalized Recommendations:\n\n")
            for rec in recommendations:
                self.advice_text.insert(tk.END, f"• {rec}\n")
            
        except Exception as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")
            
    def create_medical_tab(self):
        # Medical advice display
        self.advice_text = scrolledtext.ScrolledText(self.medical_frame, 
                                                height=15, width=80,
                                                wrap=tk.WORD, 
                                                bg='#ffffff', fg='#2c3e50',
                                                font=('Arial', 11))
        self.advice_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # PDF generation button
        ttk.Button(self.predict_frame, 
                text="Generate PDF Report", 
                command=self.generate_pdf_report,
                style='Accent.TButton').grid(row=10, column=0, columnspan=2, pady=10)
        
    def get_medical_recommendations(self, prediction, inputs):
        recommendations = []
        
        # General recommendations
        if prediction == 1:
            recommendations.append("🟥 Medical Alert: Predictive results indicate diabetes risk. Please consult a healthcare professional immediately.")
            recommendations.append("🔔 Recommendation: Schedule fasting blood glucose and HbA1c tests with your doctor.")
        else:
            recommendations.append("🟩 Predictive results show no diabetes risk. Maintain regular checkups.")
        
        # BMI-based recommendations
        bmi = inputs.get('bmi', 0)
        if bmi >= 25:
            recommendations.append("⚖️ Weight Management: Aim for 5-10% weight loss through diet and exercise")
            recommendations.append("🏃 Exercise: 150 mins/week moderate activity (brisk walking, cycling)")
        elif bmi < 18.5:
            recommendations.append("⚖️ Nutrition: Consult dietitian for healthy weight gain strategies")
        
        # Blood glucose specific
        glucose = inputs.get('blood_glucose_level', 0)
        if glucose > 140:
            recommendations.append("🍬 Blood Sugar Management: Monitor fasting and post-meal glucose levels regularly")
        
        # Smoking recommendations
        if inputs.get('smoking_history', '') in ['current', 'former']:
            recommendations.append("🚭 Smoking Cessation: Consider nicotine replacement therapy or counseling")
        
        # Hypertension management
        if inputs.get('hypertension', 0) == 1:
            recommendations.append("❤️ Blood Pressure: Maintain sodium intake <2g/day and monitor BP weekly")
        
        return recommendations

        
    def generate_pdf_report(self):
        try:
            # Collect patient data
            patient_data = {field: self.entries[field].get() for field in self.entries}
            # prediction = "Diabetic" if "Diabetic" in self.result_label.cget("text") else "Not Diabetic"
            result_text = self.result_label.cget("text")
            prediction = result_text.split(": ")[-1]
            
            # Get medical recommendations
            recommendations = self.get_medical_recommendations(
                prediction, 
                {k: float(v) if v.replace('.','',1).isdigit() else v 
                for k,v in patient_data.items()}
            )
            
            # Generate automatic filename with timestamp
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f"Diabetes_Report_{timestamp}.pdf"
            desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop', filename)
            
            # Create PDF
            # file_path = filedialog.asksaveasfilename(
            #     defaultextension=".pdf",
            #     filetypes=[("PDF files", "*.pdf")],
            #     title="Save Medical Report"
            # )
            # if not file_path:
            #     return

            # doc = SimpleDocTemplate(file_path, pagesize=letter)
            doc = SimpleDocTemplate(desktop_path, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []
            
            # Title
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Heading1'],
                alignment=1,
                spaceAfter=14
            )
            elements.append(Paragraph("Diabetes Risk Assessment Report", title_style))
            
            # Patient Information Table
            patient_table = [
                ["Patient Information", "Value"],
                ["Age", patient_data['age']],
                ["Gender", patient_data['gender']],
                ["BMI", patient_data['bmi']],
                ["HbA1c Level", patient_data['HbA1c_level']],
                ["Blood Glucose", patient_data['blood_glucose_level']],
                ["Prediction Result", prediction]
            ]
            
            table = Table(patient_table)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.black),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                ('GRID', (0,0), (-1,-1), 1, colors.black)
            ]))
            elements.append(table)
            elements.append(Spacer(1, 0.3*inch))
            
            # Medical Recommendations
            elements.append(Paragraph("Medical Recommendations:", styles['Heading2']))
            for rec in recommendations:
                elements.append(Paragraph(f"• {rec}", styles['BodyText']))
                elements.append(Spacer(1, 0.1*inch))
            
            # Disclaimer
            disclaimer = """<font color=red><i>Note: This automated report is not a substitute for professional medical advice. 
                        Always consult a qualified healthcare provider for diagnosis and treatment.</i></font>"""
            elements.append(Paragraph(disclaimer, styles['Italic']))
            
            doc.build(elements)
        #     messagebox.showinfo("Success", f"PDF report saved successfully at:\n{file_path}")
            
        # except Exception as e:
        #     messagebox.showerror("Error", f"Failed to generate PDF: {str(e)}")
        
         # Open PDF in default browser
            webbrowser.open_new_tab(f"file://{desktop_path}")
            
            # Show success message with path
            # messagebox.showinfo(
            #     "Report Generated", 
            #     f"PDF report automatically saved to:\n{desktop_path}\n"
            #     "Opened in your default browser."
            # )
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF: {str(e)}")
            
    def generate_csv_report(self):
        try:
            # Get selected dates
            start = self.start_date.get_date()
            end = self.end_date.get_date()
            
            # Convert to SQLite compatible format
            start_str = start.strftime('%Y-%m-%d')
            end_str = end.strftime('%Y-%m-%d')
            
            # Query database
            cursor = self.conn.cursor()
            cursor.execute('''SELECT 
                           id, gender, age, hypertension, heart_disease, smoking_history,
                           bmi, HbA1c_level, blood_glucose_level, prediction_result
                           FROM predictions 
                        WHERE date(timestamp) BETWEEN ? AND ?''', 
                        (start_str, end_str))
            data = cursor.fetchall()
            
            if not data:
                self.report_status.config(text="No records found in selected period", foreground='red')
                return
                
            # CSV headers
            columns = ['ID', 'Gender', 'Age', 'Hypertension', 'Heart Disease',
                    'Smoking History', 'BMI', 'HbA1c Level', 'Blood Glucose Level',
                    'Prediction Result']
            
            # Generate filename with dates
            filename = f"diabetes_report_{start_str}_to_{end_str}.csv"
            file_path = os.path.join(os.getcwd(), filename)  # Current directory

            
            # Write to CSV
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                writer.writerows(data)
                
            # Show success message
            self.report_status.config(text=f"Report saved to: {file_path}", foreground='green')
            webbrowser.open(file_path)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")




if __name__ == "__main__":
    root = tk.Tk()
    app = DiabetesPredictorApp(root)
    root.mainloop()
