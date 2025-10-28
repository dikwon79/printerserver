import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import webbrowser
from datetime import datetime
import os
import tempfile
import subprocess
import socket
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 라벨 설정 (10cm x 5cm)
LABEL_WIDTH = 10 * cm
LABEL_HEIGHT = 5 * cm

class LabelPrinter:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def create_label_pdf(self, data):
        """라벨 PDF 생성"""
        print(f"=== PDF 생성 디버깅 ===")
        print(f"입력 데이터: {data}")
        
        # 임시 PDF 파일 생성
        pdf_path = os.path.join(self.temp_dir, f"label_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        print(f"PDF 파일 경로: {pdf_path}")
        
        try:
            # PDF 캔버스 생성
            c = canvas.Canvas(pdf_path, pagesize=(LABEL_WIDTH, LABEL_HEIGHT))
            print(f"PDF 캔버스 생성 성공: {LABEL_WIDTH}x{LABEL_HEIGHT}")
        except Exception as e:
            print(f"❌ PDF 캔버스 생성 실패: {e}")
            raise
        
        # 폰트 설정
        c.setFont("Helvetica-Bold", 16)
        
        # 배경 테두리 그리기
        c.rect(0.2*cm, 0.2*cm, LABEL_WIDTH-0.4*cm, LABEL_HEIGHT-0.4*cm)
        
        # 제품명 (상단)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(0.5*cm, LABEL_HEIGHT-1.2*cm, "제품 라벨")
        
        # 순수무게 (중앙, 가장 큰 글씨)
        if 'net_weight' in data and data['net_weight']:
            c.setFont("Helvetica-Bold", 28)
            net_weight_text = f"{data['net_weight']} kg"
            text_width = c.stringWidth(net_weight_text, "Helvetica-Bold", 28)
            x_pos = (LABEL_WIDTH - text_width) / 2
            c.drawString(x_pos, LABEL_HEIGHT/2 + 0.3*cm, net_weight_text)
        
        # 총무게와 팔렛무게 (중앙 하단)
        c.setFont("Helvetica", 10)
        if 'total_weight' in data and data['total_weight']:
            total_text = f"총무게: {data['total_weight']} kg"
            c.drawString(0.5*cm, LABEL_HEIGHT/2 - 0.5*cm, total_text)
        
        if 'pallet_weight' in data and data['pallet_weight']:
            pallet_text = f"팔렛무게: {data['pallet_weight']} kg"
            c.drawString(0.5*cm, LABEL_HEIGHT/2 - 0.8*cm, pallet_text)
        
        # 날짜 (하단 좌측)
        if 'date' in data and data['date']:
            c.setFont("Helvetica", 9)
            c.drawString(0.5*cm, 0.8*cm, f"날짜: {data['date']}")
        
        # 인쇄 시간 (우측 하단)
        c.setFont("Helvetica", 8)
        c.drawString(LABEL_WIDTH-3*cm, 0.5*cm, f"시간: {datetime.now().strftime('%H:%M:%S')}")
        
        c.save()
        print(f"✅ PDF 저장 완료: {pdf_path}")
        
        # 파일 존재 여부 확인
        if os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path)
            print(f"✅ PDF 파일 확인됨 - 크기: {file_size} bytes")
        else:
            print(f"❌ PDF 파일이 생성되지 않았습니다!")
            
        return pdf_path
    
    def print_label(self, pdf_path, printer_name=None, label_data=None):
        """라벨 인쇄"""
        try:
            # CUPS를 통한 인쇄 (Linux/macOS)
            if os.name == 'posix':
                cmd = ['lp']
                if printer_name:
                    cmd.extend(['-d', printer_name])
                cmd.append(pdf_path)
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info(f"라벨이 성공적으로 인쇄되었습니다: {pdf_path}")
                    return True
                else:
                    logger.error(f"인쇄 실패: {result.stderr}")
                    return False
            else:
                # Windows의 경우 - PDF로 인쇄
                if printer_name:
                    print(f"Windows 인쇄 시도 - 프린터: {printer_name}")
                    return self.print_simple_pdf(pdf_path, printer_name)
                else:
                    # 기본 프린터로 인쇄
                    os.startfile(pdf_path, "print")
                    logger.info(f"라벨이 기본 프린터로 인쇄되었습니다: {pdf_path}")
                    return True
        except Exception as e:
            logger.error(f"인쇄 중 오류 발생: {str(e)}")
            return False
    
    def print_simple_pdf(self, pdf_path, printer_name):
        """선택된 프린터로 PDF 인쇄"""
        try:
            import win32print
            
            print(f"=== 프린터 인쇄 디버깅 ===")
            print(f"요청된 프린터: {printer_name}")
            print(f"PDF 파일 경로: {pdf_path}")
            
            # 사용 가능한 프린터 목록 확인
            printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
            printer_names = [printer[2] for printer in printers]
            print(f"시스템에 설치된 프린터 목록: {printer_names}")
            
            # 현재 기본 프린터 저장
            original_default = win32print.GetDefaultPrinter()
            print(f"현재 기본 프린터: {original_default}")
            
            # 프린터 존재 여부 확인
            if printer_name not in printer_names:
                print(f"❌ 프린터 '{printer_name}'를 찾을 수 없습니다!")
                print(f"사용 가능한 프린터: {printer_names}")
                
                # 가장 비슷한 프린터 찾기
                similar_printers = [p for p in printer_names if printer_name.lower() in p.lower() or p.lower() in printer_name.lower()]
                if similar_printers:
                    print(f"비슷한 프린터 발견: {similar_printers}")
                    printer_name = similar_printers[0]
                    print(f"프린터를 '{printer_name}'로 변경하여 시도합니다.")
                else:
                    print("기본 프린터로 인쇄합니다.")
                    os.startfile(pdf_path, 'print')
                    return True
            
            # 선택된 프린터를 기본 프린터로 임시 변경
            try:
                win32print.SetDefaultPrinter(printer_name)
                print(f"✅ 기본 프린터를 '{printer_name}'로 임시 변경 성공")
                
                # 변경 확인
                current_default = win32print.GetDefaultPrinter()
                print(f"변경 후 기본 프린터: {current_default}")
                
            except Exception as e:
                print(f"❌ 기본 프린터 변경 실패: {e}")
                print("기본 프린터로 인쇄합니다.")
                os.startfile(pdf_path, 'print')
                return True
            
            # PDF 인쇄 - 더 확실한 방법 사용
            print("PDF 인쇄 시작...")
            
            # 방법 1: win32api를 사용하여 직접 프린터로 전송
            try:
                import win32api
                print(f"win32api로 프린터 '{printer_name}'에 직접 전송 시도...")
                win32api.ShellExecute(0, "print", pdf_path, f'/d:"{printer_name}"', ".", 0)
                print(f"✅ win32api로 PDF가 프린터로 전송되었습니다: {printer_name}")
            except ImportError:
                print("win32api 없음, 기본 방법 사용...")
                os.startfile(pdf_path, 'print')
                print(f"✅ PDF가 기본 프린터로 전송되었습니다")
            except Exception as e:
                print(f"win32api 실패: {e}, 기본 방법 사용...")
                os.startfile(pdf_path, 'print')
                print(f"✅ PDF가 기본 프린터로 전송되었습니다")
            
            # 잠시 대기 후 원래 기본 프린터로 복원
            import time
            time.sleep(3)  # 인쇄 시간을 고려하여 3초로 증가
            
            try:
                win32print.SetDefaultPrinter(original_default)
                print(f"✅ 기본 프린터 복원 성공: {original_default}")
            except Exception as e:
                print(f"⚠️ 기본 프린터 복원 실패: {e}")
            
            logger.info(f"프린터 '{printer_name}'로 PDF 인쇄 성공")
            return True
            
        except ImportError:
            print("❌ win32print 모듈이 없습니다. pip install pywin32로 설치해주세요.")
            # win32print가 없으면 기본 방법으로 인쇄
            os.startfile(pdf_path, "print")
            logger.info(f"PDF가 기본 프린터로 인쇄됨: {pdf_path}")
            return True
            
        except Exception as e:
            logger.error(f"PDF 인쇄 실패: {e}")
            print(f"❌ 인쇄 중 오류 발생: {e}")
            
            # 오류 발생 시 기본 방법으로 인쇄
            try:
                print("기본 방법으로 인쇄 시도...")
                os.startfile(pdf_path, "print")
                logger.info(f"PDF가 기본 프린터로 인쇄됨: {pdf_path}")
                return True
            except Exception as e2:
                logger.error(f"기본 인쇄도 실패: {e2}")
                return False
    
    
    

class LabelPrinterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("라벨 인쇄 프로그램")
        self.root.geometry("600x700")
        self.root.resizable(True, True)
        
        # 프린터 인스턴스
        self.printer = LabelPrinter()
        
        # Flask 서버 관련
        self.flask_app = None
        self.server_thread = None
        self.server_running = False
        
        # 인쇄 기록 저장
        self.print_history = []
        
        # 서버 IP 자동 감지
        self.server_ip = self.get_local_ip()
        self.server_port = self.find_available_port()
        
        # GUI 구성
        self.setup_gui()
        
        # 서버 시작
        self.start_server()
    
    def get_local_ip(self):
        """로컬 IP 주소 자동 감지"""
        try:
            # 외부 서버에 연결하여 로컬 IP 확인
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                return local_ip
        except Exception:
            try:
                # 대안 방법: 호스트명으로 IP 확인
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                if local_ip.startswith("127."):
                    # 루프백 주소인 경우 다른 방법 시도
                    import subprocess
                    if os.name == 'posix':  # macOS/Linux
                        result = subprocess.run(['ifconfig'], capture_output=True, text=True)
                        for line in result.stdout.split('\n'):
                            if 'inet ' in line and '127.0.0.1' not in line:
                                ip = line.split()[1]
                                if not ip.startswith('127.'):
                                    return ip
                    else:  # Windows
                        result = subprocess.run(['ipconfig'], capture_output=True, text=True)
                        for line in result.stdout.split('\n'):
                            if 'IPv4' in line and '127.0.0.1' not in line:
                                ip = line.split(':')[-1].strip()
                                if not ip.startswith('127.'):
                                    return ip
                return local_ip
            except Exception:
                return "127.0.0.1"  # 최후의 수단
    
    def find_available_port(self):
        """사용 가능한 포트 찾기"""
        import socket
        
        # 시도할 포트 목록
        ports_to_try = [8080, 8081, 8082, 8083, 8084, 5000, 5001, 5002, 5003, 5004]
        
        for port in ports_to_try:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((self.server_ip, port))
                    return port
            except OSError:
                continue
        
        # 모든 포트가 사용 중인 경우 시스템이 자동으로 할당하도록 0 반환
        return 0
        
    def setup_gui(self):
        """GUI 구성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 제목
        title_label = ttk.Label(main_frame, text="라벨 인쇄 프로그램", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 서버 상태
        self.setup_server_status(main_frame)
        
        # 라벨 입력 폼
        self.setup_label_form(main_frame)
        
        # 버튼들
        self.setup_buttons(main_frame)
        
        # 프린터 정보
        self.setup_printer_info(main_frame)
        
        # 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
    def setup_server_status(self, parent):
        """서버 상태 섹션"""
        status_frame = ttk.LabelFrame(parent, text="서버 상태", padding="10")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="서버 시작 중...", foreground="orange")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.server_url_label = ttk.Label(status_frame, text="", font=("Arial", 9))
        self.server_url_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
    def setup_label_form(self, parent):
        """라벨 입력 폼"""
        form_frame = ttk.LabelFrame(parent, text="라벨 정보 입력", padding="10")
        form_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        form_frame.columnconfigure(1, weight=1)
        
        # 총무게
        ttk.Label(form_frame, text="총무게 (kg):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.total_weight_var = tk.StringVar()
        self.total_weight_entry = ttk.Entry(form_frame, textvariable=self.total_weight_var, width=30)
        self.total_weight_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))
        self.total_weight_var.trace_add('write', self.calculate_net_weight)
        
        # 팔렛무게
        ttk.Label(form_frame, text="팔렛무게 (kg):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.pallet_weight_var = tk.StringVar()
        self.pallet_weight_entry = ttk.Entry(form_frame, textvariable=self.pallet_weight_var, width=30)
        self.pallet_weight_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))
        self.pallet_weight_var.trace_add('write', self.calculate_net_weight)
        
        # 순수무게 (자동 계산)
        ttk.Label(form_frame, text="순수무게 (kg):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.net_weight_var = tk.StringVar()
        self.net_weight_label = ttk.Label(form_frame, textvariable=self.net_weight_var, foreground="blue", font=("Arial", 10, "bold"))
        self.net_weight_label.grid(row=2, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        # 날짜 (자동 설정)
        ttk.Label(form_frame, text="날짜:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        self.date_label = ttk.Label(form_frame, textvariable=self.date_var, foreground="gray")
        self.date_label.grid(row=3, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        # 프린터 선택
        ttk.Label(form_frame, text="프린터 선택:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.printer_var = tk.StringVar()
        self.printer_combo = ttk.Combobox(form_frame, textvariable=self.printer_var, state="readonly", width=27)
        self.printer_combo.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))
        
    def setup_buttons(self, parent):
        """버튼들"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="라벨 인쇄", command=self.print_label).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="미리보기", command=self.preview_label).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="초기화", command=self.reset_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="PDF 저장", command=self.save_pdf).pack(side=tk.LEFT, padx=5)
        
    def setup_printer_info(self, parent):
        """프린터 정보"""
        printer_frame = ttk.LabelFrame(parent, text="인쇄 기록", padding="10")
        printer_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        printer_frame.columnconfigure(0, weight=1)
        
        # 인쇄 기록 목록
        ttk.Label(printer_frame, text="최근 인쇄 기록:").grid(row=0, column=0, sticky=tk.W)
        
        self.print_history_listbox = tk.Listbox(printer_frame, height=6)
        self.print_history_listbox.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # 기록 초기화 버튼
        ttk.Button(printer_frame, text="기록 초기화", command=self.clear_print_history).grid(row=2, column=0, pady=(5, 0))
        
        # 초기 프린터 목록 로드
        self.refresh_printers()
        
    def calculate_net_weight(self, *args):
        """순수무게 자동 계산"""
        try:
            total_weight = float(self.total_weight_var.get() or 0)
            pallet_weight = float(self.pallet_weight_var.get() or 0)
            net_weight = total_weight - pallet_weight
            
            if net_weight > 0:
                self.net_weight_var.set(f"{net_weight:.2f} kg")
            else:
                self.net_weight_var.set("0.00 kg")
        except ValueError:
            self.net_weight_var.set("0.00 kg")
    
    def reset_form(self):
        """폼 초기화"""
        self.total_weight_var.set("")
        self.pallet_weight_var.set("")
        self.net_weight_var.set("0.00 kg")
        self.date_var.set(datetime.now().strftime('%Y-%m-%d'))
        
    def get_label_data(self):
        """입력된 라벨 데이터 가져오기"""
        try:
            total_weight = float(self.total_weight_var.get() or 0)
            pallet_weight = float(self.pallet_weight_var.get() or 0)
            net_weight = total_weight - pallet_weight
        except ValueError:
            net_weight = 0
            
        return {
            'total_weight': self.total_weight_var.get(),
            'pallet_weight': self.pallet_weight_var.get(),
            'net_weight': f"{net_weight:.2f}",
            'weight': f"{net_weight:.2f}",  # 라벨에 표시될 무게 (순수무게)
            'date': self.date_var.get(),
            'printer': self.printer_var.get(),
            'product_name': '제품'  # 기본값
        }
        
    def validate_data(self, data):
        """데이터 유효성 검사"""
        if not data['total_weight']:
            messagebox.showerror("오류", "총무게를 입력해주세요.")
            return False
            
        if not data['pallet_weight']:
            messagebox.showerror("오류", "팔렛무게를 입력해주세요.")
            return False
            
        if not data['printer']:
            messagebox.showerror("오류", "프린터를 선택해주세요.")
            return False
        
        try:
            total_weight = float(data['total_weight'])
            pallet_weight = float(data['pallet_weight'])
            
            if total_weight <= 0:
                messagebox.showerror("오류", "총무게는 0보다 큰 값이어야 합니다.")
                return False
                
            if pallet_weight < 0:
                messagebox.showerror("오류", "팔렛무게는 0 이상이어야 합니다.")
                return False
                
            if pallet_weight >= total_weight:
                messagebox.showerror("오류", "팔렛무게는 총무게보다 작아야 합니다.")
                return False
                
        except ValueError:
            messagebox.showerror("오류", "무게는 숫자여야 합니다.")
            return False
            
        return True
        
    def print_label(self):
        """라벨 인쇄"""
        data = self.get_label_data()
        
        if not self.validate_data(data):
            return
            
        try:
            # PDF 생성
            pdf_path = self.printer.create_label_pdf(data)
            
            # 실제 프린터 이름 가져오기
            display_name = data['printer']
            actual_printer_name = self.printer_names.get(display_name, None)
            
            # 디버깅 정보 출력
            print(f"선택된 프린터 표시명: {display_name}")
            print(f"실제 프린터명: {actual_printer_name}")
            print(f"사용 가능한 프린터 매핑: {self.printer_names}")
            
            # 인쇄 실행 (라벨 데이터도 함께 전달)
            success = self.printer.print_label(pdf_path, actual_printer_name, data)
            
            if success:
                # 인쇄 기록 저장
                self.save_print_record(data)
                
                # 프린터 타입에 따른 메시지
                if actual_printer_name:
                    messagebox.showinfo("성공", f"프린터 '{actual_printer_name}'로 라벨이 성공적으로 인쇄되었습니다.")
                else:
                    messagebox.showinfo("성공", "라벨이 성공적으로 인쇄되었습니다.\n(기본 프린터로 인쇄됨)")
            else:
                messagebox.showerror("오류", "인쇄에 실패했습니다. 프린터 설정을 확인해주세요.")
                
        except Exception as e:
            messagebox.showerror("오류", f"인쇄 중 오류가 발생했습니다: {str(e)}")
            
    def preview_label(self):
        """라벨 미리보기"""
        data = self.get_label_data()
        
        if not self.validate_data(data):
            return
            
        try:
            # PDF 생성
            pdf_path = self.printer.create_label_pdf(data)
            
            # PDF 뷰어로 열기
            if os.name == 'posix':
                subprocess.run(['open', pdf_path])  # macOS
            else:
                os.startfile(pdf_path)  # Windows
                
        except Exception as e:
            messagebox.showerror("오류", f"미리보기 생성 중 오류가 발생했습니다: {str(e)}")
            
    def save_pdf(self):
        """PDF 파일로 저장"""
        data = self.get_label_data()
        
        if not self.validate_data(data):
            return
            
        try:
            # 저장할 파일 경로 선택
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                title="라벨 PDF 저장"
            )
            
            if filename:
                # PDF 생성
                pdf_path = self.printer.create_label_pdf(data)
                
                # 파일 복사
                import shutil
                shutil.copy2(pdf_path, filename)
                
                messagebox.showinfo("성공", f"PDF가 저장되었습니다: {filename}")
                
        except Exception as e:
            messagebox.showerror("오류", f"PDF 저장 중 오류가 발생했습니다: {str(e)}")
            
    def refresh_printers(self):
        """프린터 목록 새로고침"""
        printer_list = []
        self.printer_names = {}  # 표시명 -> 실제 프린터명 매핑
        
        try:
            if os.name == 'posix':
                result = subprocess.run(['lpstat', '-p'], capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if line.startswith('printer'):
                            parts = line.split()
                            if len(parts) >= 2:
                                printer_name = parts[1]
                                status = '사용 가능' if 'idle' in line else '사용 중'
                                display_name = f"{printer_name} ({status})"
                                printer_list.append(display_name)
                                self.printer_names[display_name] = printer_name
                else:
                    printer_list.append("기본 프린터")
                    self.printer_names["기본 프린터"] = None
            else:
                # Windows의 경우 - win32print를 사용하여 프린터 목록 조회
                try:
                    import win32print
                    
                    # win32print로 프린터 목록 조회
                    printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
                    
                    for printer in printers:
                        printer_name = printer[2]  # 프린터 이름
                        if printer_name:
                            display_name = f"{printer_name} (사용 가능)"
                            printer_list.append(display_name)
                            self.printer_names[display_name] = printer_name
                    
                    print(f"win32print로 발견된 프린터: {[p[2] for p in printers]}")
                    
                except ImportError:
                    print("win32print 모듈이 없습니다. PowerShell로 프린터 목록 조회...")
                    
                    # 방법 1: PowerShell로 프린터 목록 조회
                    ps_command = "Get-Printer | ForEach-Object { $_.Name }"
                    result = subprocess.run([
                        'powershell', '-Command', ps_command
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0 and result.stdout.strip():
                        printer_names = result.stdout.strip().split('\n')
                        for printer_name in printer_names:
                            printer_name = printer_name.strip()
                            if printer_name:
                                display_name = f"{printer_name} (사용 가능)"
                                printer_list.append(display_name)
                                self.printer_names[display_name] = printer_name
                    
                    # 방법 2: wmic 명령어로도 시도
                    if not printer_list:
                        wmic_result = subprocess.run([
                            'wmic', 'printer', 'get', 'name', '/format:list'
                        ], capture_output=True, text=True, timeout=10)
                        
                        if wmic_result.returncode == 0:
                            for line in wmic_result.stdout.split('\n'):
                                if line.startswith('Name='):
                                    printer_name = line.replace('Name=', '').strip()
                                    if printer_name and printer_name != '':
                                        display_name = f"{printer_name} (사용 가능)"
                                        printer_list.append(display_name)
                                        self.printer_names[display_name] = printer_name
                
                # 프린터가 없으면 기본 프린터 추가
                if not printer_list:
                        printer_list.append("기본 프린터")
                        self.printer_names["기본 프린터"] = None
                
                print(f"win32print로 발견된 프린터: {printer_list}")
                
        except Exception as e:
            printer_list.append("기본 프린터")
            self.printer_names["기본 프린터"] = None
        
        # 콤보박스 업데이트
        self.printer_combo['values'] = printer_list
        if printer_list:
            # 현재 선택된 값이 없거나 목록에 없으면 첫 번째 항목 선택
            current_value = self.printer_var.get()
            if not current_value or current_value not in printer_list:
                self.printer_combo.current(0)
                self.printer_var.set(printer_list[0])
    
    def save_print_record(self, data):
        """인쇄 기록 저장"""
        record = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_weight': data['total_weight'],
            'pallet_weight': data['pallet_weight'],
            'net_weight': data['net_weight'],
            'printer': data['printer'],
            'date': data['date']
        }
        
        self.print_history.insert(0, record)  # 최신 기록을 맨 위에 추가
        
        # 최대 50개 기록만 유지
        if len(self.print_history) > 50:
            self.print_history = self.print_history[:50]
        
        # 기록 목록 업데이트
        self.update_print_history_display()
    
    def update_print_history_display(self):
        """인쇄 기록 표시 업데이트"""
        self.print_history_listbox.delete(0, tk.END)
        
        for record in self.print_history:
            display_text = f"{record['timestamp']} | 총:{record['total_weight']}kg 팔렛:{record['pallet_weight']}kg 순수:{record['net_weight']}kg | {record['printer']}"
            self.print_history_listbox.insert(tk.END, display_text)
    
    def clear_print_history(self):
        """인쇄 기록 초기화"""
        self.print_history = []
        self.update_print_history_display()
            
    def start_server(self):
        """Flask 서버 시작"""
        def run_server():
            self.flask_app = Flask(__name__)
            CORS(self.flask_app)
            
            # API 엔드포인트들
            self.setup_api_endpoints()
            
            self.server_running = True
            self.flask_app.run(host=self.server_ip, port=self.server_port, debug=False, use_reloader=False)
            
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        # 서버 상태 업데이트
        self.root.after(1000, self.update_server_status)
        
    def setup_api_endpoints(self):
        """API 엔드포인트 설정"""
        app = self.flask_app
        
        @app.route('/api/status', methods=['GET'])
        def server_status():
            return jsonify({
                'success': True,
                'status': 'running',
                'server_time': datetime.now().isoformat(),
                'version': '1.0.0',
                'label_size': '10cm x 5cm'
            })
            
        @app.route('/api/print', methods=['POST'])
        def print_label_api():
            try:
                data = request.get_json()
                
                if not data.get('total_weight'):
                    return jsonify({
                        'success': False,
                        'error': 'TOTAL_WEIGHT_REQUIRED',
                        'message': '총무게 정보가 필요합니다.'
                    }), 400
                    
                if not data.get('pallet_weight'):
                    return jsonify({
                        'success': False,
                        'error': 'PALLET_WEIGHT_REQUIRED',
                        'message': '팔렛무게 정보가 필요합니다.'
                    }), 400
                
                # 순수무게 계산
                try:
                    total_weight = float(data['total_weight'])
                    pallet_weight = float(data['pallet_weight'])
                    net_weight = total_weight - pallet_weight
                    
                    if net_weight <= 0:
                        return jsonify({
                            'success': False,
                            'error': 'INVALID_WEIGHT',
                            'message': '팔렛무게가 총무게보다 크거나 같습니다.'
                        }), 400
                        
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': 'INVALID_WEIGHT_FORMAT',
                        'message': '무게는 숫자여야 합니다.'
                    }), 400
                
                # 기본값 설정
                data['net_weight'] = f"{net_weight:.2f}"
                data['weight'] = f"{net_weight:.2f}"  # 라벨에 표시될 무게
                if not data.get('date'):
                    data['date'] = datetime.now().strftime('%Y-%m-%d')
                if not data.get('product_name'):
                    data['product_name'] = '제품'
                if not data.get('printer'):
                    data['printer'] = '기본 프린터'
                
                # PDF 생성
                pdf_path = self.printer.create_label_pdf(data)
                
                # 실제 프린터 이름 가져오기
                display_name = data.get('printer', '기본 프린터')
                
                # API에서는 프린터 이름을 직접 사용 (GUI의 매핑 없이)
                if display_name == '기본 프린터' or display_name == 'default':
                    actual_printer_name = None  # 기본 프린터 사용
                else:
                    actual_printer_name = display_name  # 프린터 이름 직접 사용
                
                print(f"API 인쇄 - 선택된 프린터: {display_name}")
                print(f"API 인쇄 - 실제 프린터명: {actual_printer_name}")
                
                # 인쇄 실행 (라벨 데이터도 함께 전달)
                success = self.printer.print_label(pdf_path, actual_printer_name, data)
                
                if success:
                    # 인쇄 기록 저장
                    self.save_print_record(data)
                    
                    return jsonify({
                        'success': True,
                        'message': '라벨이 성공적으로 인쇄되었습니다.',
                        'data': {
                            'total_weight': data.get('total_weight'),
                            'pallet_weight': data.get('pallet_weight'),
                            'net_weight': data.get('net_weight'),
                            'printer': data.get('printer'),
                            'print_time': datetime.now().isoformat()
                        }
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'PRINT_FAILED',
                        'message': '인쇄에 실패했습니다. 프린터 설정을 확인해주세요.'
                    }), 500
                    
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': 'INTERNAL_ERROR',
                    'message': f'서버 오류가 발생했습니다: {str(e)}'
                }), 500
                
        @app.route('/api/printers', methods=['GET'])
        def list_printers():
            try:
                # Windows 테스트를 위해 강제로 Windows 경로 사용
                force_windows = request.args.get('force_windows', 'false').lower() == 'true'
                
                if os.name == 'posix' and not force_windows:
                    result = subprocess.run(['lpstat', '-p'], capture_output=True, text=True)
                    if result.returncode == 0:
                        printers = []
                        for line in result.stdout.split('\n'):
                            if line.startswith('printer'):
                                parts = line.split()
                                if len(parts) >= 2:
                                    printer_name = parts[1]
                                    status = 'available' if 'idle' in line else 'busy'
                                    printers.append({
                                        'name': printer_name,
                                        'status': status,
                                        'description': f'프린터 {printer_name}'
                                    })
                        return jsonify({'success': True, 'printers': printers})
                    else:
                        return jsonify({'success': True, 'printers': []})
                else:
                    # Windows의 경우 - GUI와 동일한 로직 사용
                    printers = []
                    try:
                        # 방법 1: PowerShell로 프린터 목록 조회
                        ps_command = "Get-Printer | ForEach-Object { $_.Name }"
                        result = subprocess.run([
                            'powershell', '-Command', ps_command
                        ], capture_output=True, text=True, timeout=10)
                        
                        print(f"PowerShell 결과: {result.returncode}, 출력: {result.stdout}")
                        
                        if result.returncode == 0 and result.stdout.strip():
                            printer_names = result.stdout.strip().split('\n')
                            for printer_name in printer_names:
                                printer_name = printer_name.strip()
                                if printer_name:
                                    printers.append({
                                        'name': printer_name,
                                        'status': 'available',
                                        'description': f'프린터 {printer_name}'
                                    })
                        
                        # 방법 2: wmic 명령어로도 시도
                        if not printers:
                            print("PowerShell 실패, WMIC 시도 중...")
                            wmic_result = subprocess.run([
                                'wmic', 'printer', 'get', 'name', '/format:list'
                            ], capture_output=True, text=True, timeout=10)
                            
                            print(f"WMIC 결과: {wmic_result.returncode}, 출력: {wmic_result.stdout}")
                            
                            if wmic_result.returncode == 0:
                                for line in wmic_result.stdout.split('\n'):
                                    if line.startswith('Name='):
                                        printer_name = line.replace('Name=', '').strip()
                                        if printer_name and printer_name != '':
                                            printers.append({
                                                'name': printer_name,
                                                'status': 'available',
                                                'description': f'프린터 {printer_name}'
                                            })
                        
                        # 방법 3: 레지스트리에서 프린터 목록 조회 (Windows 전용)
                        if not printers:
                            print("WMIC 실패, 레지스트리 시도 중...")
                            try:
                                import winreg
                                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Print\Printers")
                                i = 0
                                while True:
                                    try:
                                        printer_name = winreg.EnumKey(key, i)
                                        printers.append({
                                            'name': printer_name,
                                            'status': 'available',
                                            'description': f'프린터 {printer_name}'
                                        })
                                        i += 1
                                    except WindowsError:
                                        break
                                winreg.CloseKey(key)
                            except ImportError:
                                print("winreg 모듈을 사용할 수 없습니다 (Windows가 아님)")
                        
                        # 프린터가 없으면 기본 프린터 추가
                        if not printers:
                            print("모든 방법 실패, 기본 프린터 추가")
                            printers.append({
                                'name': 'default',
                                'status': 'available',
                                'description': '기본 프린터'
                            })
                            
                    except Exception as e:
                        print(f"Windows 프린터 조회 오류: {e}")
                        printers.append({
                            'name': 'default',
                            'status': 'available',
                            'description': '기본 프린터'
                        })
                    
                    print(f"최종 프린터 목록: {printers}")
                    return jsonify({'success': True, 'printers': printers})
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': 'PRINTER_LIST_FAILED',
                    'message': f'프린터 목록 조회 실패: {str(e)}'
                }), 500
                
    def update_server_status(self):
        """서버 상태 업데이트"""
        if self.server_running:
            self.status_label.config(text="서버 실행 중", foreground="green")
            self.server_url_label.config(text=f"모바일 앱에서 접속 가능: http://{self.server_ip}:{self.server_port}")
        else:
            self.status_label.config(text="서버 중지됨", foreground="red")
            self.server_url_label.config(text="")
            
        # 5초마다 상태 업데이트
        self.root.after(5000, self.update_server_status)
        
    def on_closing(self):
        """프로그램 종료 시"""
        self.server_running = False
        self.root.destroy()

def main():
    root = tk.Tk()
    app = LabelPrinterGUI(root)
    
    # 종료 이벤트 처리
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    root.mainloop()

if __name__ == "__main__":
    main()
