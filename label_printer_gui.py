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
    
    def print_image(self, image_path, printer_name, label_width_cm=None, label_height_cm=None):
        """이미지를 지정된 프린터로 직접 인쇄 (Word/한글 방식)
        
        Args:
            image_path: 인쇄할 이미지 파일 경로
            printer_name: 프린터 이름
            label_width_cm: 라벨 너비 (cm) - None이면 이미지 크기 기반으로 계산
            label_height_cm: 라벨 높이 (cm) - None이면 이미지 크기 기반으로 계산
        """
        try:
            import win32print
            import win32ui
            from PIL import Image, ImageWin
            
            print(f"이미지 인쇄 시작 - 프린터: {printer_name}")
            print(f"이미지 파일: {image_path}")
            
            # 이미지 로드
            pil_image = Image.open(image_path)
            img_width, img_height = pil_image.size
            
            # RGB 모드로 변환
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # win32print를 사용하여 이미지를 프린터로 직접 전송
            # DC(Device Context) 생성 (Word/한글이 하는 방식)
            hdc = win32ui.CreateDC()
            hdc.CreatePrinterDC(printer_name)
            
            try:
                # 인쇄 시작
                hdc.StartDoc("Label Print")
                hdc.StartPage()
                
                # 프린터 DPI 가져오기
                printer_dpi_x = hdc.GetDeviceCaps(88)  # LOGPIXELSX
                printer_dpi_y = hdc.GetDeviceCaps(90)  # LOGPIXELSY
                
                # GetDeviceCaps 상수 정의
                HORZRES = 8        # 인쇄 가능 너비
                VERTRES = 10      # 인쇄 가능 높이
                PHYSICALWIDTH = 110   # 실제 페이지 너비
                PHYSICALHEIGHT = 111  # 실제 페이지 높이
                PHYSICALOFFSETX = 112  # 왼쪽 여백
                PHYSICALOFFSETY = 113  # 위쪽 여백
                
                # 프린터의 실제 인쇄 가능 영역 가져오기
                printable_width = hdc.GetDeviceCaps(HORZRES)
                printable_height = hdc.GetDeviceCaps(VERTRES)
                
                # 프린터의 실제 페이지 크기 가져오기
                page_width = hdc.GetDeviceCaps(PHYSICALWIDTH)
                page_height = hdc.GetDeviceCaps(PHYSICALHEIGHT)
                
                # 프린터의 여백(오프셋) 가져오기
                try:
                    printer_margin_x = hdc.GetDeviceCaps(PHYSICALOFFSETX)
                    printer_margin_y = hdc.GetDeviceCaps(PHYSICALOFFSETY)
                    print(f"프린터 페이지 크기: {page_width} x {page_height} 픽셀")
                    print(f"프린터 여백: ({printer_margin_x}, {printer_margin_y}) 픽셀")
                except Exception as e:
                    printer_margin_x = 0
                    printer_margin_y = 0
                    print(f"⚠️ 프린터 여백 정보를 가져올 수 없습니다: {e}")
                    # 대안: 페이지 크기와 인쇄 가능 영역 차이로 여백 추정
                    if page_width > printable_width:
                        printer_margin_x = (page_width - printable_width) // 2
                    if page_height > printable_height:
                        printer_margin_y = (page_height - printable_height) // 2
                    print(f"추정된 프린터 여백: ({printer_margin_x}, {printer_margin_y}) 픽셀")
                
                print(f"프린터 DPI: {printer_dpi_x} x {printer_dpi_y}")
                print(f"프린터 인쇄 가능 영역: {printable_width} x {printable_height} 픽셀")
                print(f"이미지 크기: {img_width} x {img_height} 픽셀 (300 DPI 기준)")
                
                # 라벨용지 사이즈에 맞게 인쇄
                # label_width_cm, label_height_cm가 제공되면 그 값을 사용
                # 없으면 이미지의 300 DPI 기준 물리적 크기 사용
                if label_width_cm is not None and label_height_cm is not None:
                    # 라벨용지 사이즈를 인치로 변환 (1cm = 0.393701 인치)
                    physical_width_inch = label_width_cm * 0.393701
                    physical_height_inch = label_height_cm * 0.393701
                    print(f"라벨용지 사이즈 사용: {label_width_cm}cm x {label_height_cm}cm ({physical_width_inch:.2f}\" x {physical_height_inch:.2f}\")")
                else:
                    # 이미지는 300 DPI로 저장되었으므로, 물리적 크기 계산 (인치 단위)
                    physical_width_inch = img_width / 300.0
                    physical_height_inch = img_height / 300.0
                    print(f"이미지 크기 기반 계산: {physical_width_inch:.2f}\" x {physical_height_inch:.2f}\"")
                
                # 프린터 DPI에서 라벨용지 사이즈에 맞는 픽셀 수 계산
                scaled_width = int(physical_width_inch * printer_dpi_x)
                scaled_height = int(physical_height_inch * printer_dpi_y)
                
                print(f"프린터 DPI 기준 출력 크기: {scaled_width} x {scaled_height} 픽셀")
                print(f"프린터 인쇄 가능 영역: {printable_width} x {printable_height} 픽셀")
                
                # 라벨용지 사이즈에 맞게 정확히 출력
                # 인쇄 가능 영역 내에서만 출력하도록 보장
                # 비율을 유지하면서 인쇄 가능 영역에 맞게 조정
                if scaled_width > printable_width or scaled_height > printable_height:
                    # 인쇄 가능 영역보다 크면 비율을 유지하며 맞춤
                    width_ratio = printable_width / scaled_width
                    height_ratio = printable_height / scaled_height
                    scale_ratio = min(width_ratio, height_ratio)
                    
                    scaled_width = int(scaled_width * scale_ratio)
                    scaled_height = int(scaled_height * scale_ratio)
                    
                    print(f"⚠️ 이미지가 인쇄 가능 영역을 초과하여 비율 유지하며 축소: {scaled_width} x {scaled_height} 픽셀")
                else:
                    print(f"✅ 이미지 크기 OK: {scaled_width} x {scaled_height} 픽셀 (인쇄 가능 영역 내)")
                
                # PIL ImageWin을 사용하여 이미지를 프린터로 직접 그리기
                # 이미지를 프린터 DPI에 맞게 리사이즈
                # 원본 이미지를 프린터 크기에 맞게 조정
                if pil_image.size[0] != scaled_width or pil_image.size[1] != scaled_height:
                    print(f"이미지 리사이즈: {pil_image.size[0]} x {pil_image.size[1]} → {scaled_width} x {scaled_height}")
                    pil_image = pil_image.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
                
                # 인쇄 가능 영역 내에 정확히 맞도록 보장
                # 스케일된 크기가 인쇄 가능 영역을 초과하지 않도록 확인
                final_width = min(scaled_width, printable_width)
                final_height = min(scaled_height, printable_height)
                
                if final_width != scaled_width or final_height != scaled_height:
                    print(f"⚠️ 인쇄 가능 영역에 맞게 조정: {scaled_width} x {scaled_height} → {final_width} x {final_height}")
                    pil_image = pil_image.resize((final_width, final_height), Image.Resampling.LANCZOS)
                
                dib = ImageWin.Dib(pil_image)
                
                # 프린터에 이미지 그리기
                # 프린터 여백을 고려하여 이미지를 그릴 위치 결정
                # 라벨 프린터는 보통 여백이 없어야 하므로, 여백을 무시하고 (0,0)부터 그리기
                # 만약 프린터 여백이 있다면, 여백 위치에 맞춰서 그리기
                
                # 여백을 무시하고 (0, 0)부터 그리기 (라벨 프린터용)
                print_offset_x = 0
                print_offset_y = 0
                
                # 만약 프린터 여백을 고려하려면 아래 주석 해제:
                # print_offset_x = printer_margin_x
                # print_offset_y = printer_margin_y
                
                # 프린터의 실제 물리적 크기 그대로 출력
                # 인쇄 가능 영역 내에 정확히 맞춤
                target_rect = (print_offset_x, print_offset_y, 
                              print_offset_x + final_width, 
                              print_offset_y + final_height)
                dib.draw(hdc.GetHandleOutput(), target_rect)
                
                print(f"인쇄 시작 위치: ({print_offset_x}, {print_offset_y})")
                print(f"프린터 여백 정보: ({printer_margin_x}, {printer_margin_y}) - 이미지는 여백 무시하고 (0,0)부터 그려집니다")
                
                print(f"최종 인쇄 크기: {final_width} x {final_height} 픽셀")
                
                hdc.EndPage()
                hdc.EndDoc()
                
                print(f"✅ 이미지를 프린터 '{printer_name}'로 직접 전송 성공")
                logger.info(f"프린터 '{printer_name}'로 이미지 인쇄 성공")
                return True
                
            finally:
                hdc.DeleteDC()
                
        except ImportError:
            print("❌ win32print 모듈이 없습니다. pip install pywin32 pillow로 설치해주세요.")
            return False
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"이미지 인쇄 실패: {e}")
            print(f"❌ 이미지 인쇄 실패: {e}")
            return False
    
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
            
            # PDF를 특정 프린터로 직접 인쇄 (PowerShell 사용)
            print(f"PDF 인쇄 시작 - 프린터: {printer_name}")
            
            # 경로 이스케이프 처리
            pdf_path_escaped = pdf_path.replace('\\', '\\\\').replace("'", "''")
            printer_name_escaped = printer_name.replace("'", "''")
            
            try:
                # 방법 1: Adobe Reader의 /t 옵션으로 직접 프린터 지정 (가장 확실한 방법)
                print("Adobe Reader로 직접 프린터 지정 인쇄 시도...")
                
                ps_script = f'''
$pdfPath = '{pdf_path_escaped}'
$printerName = '{printer_name_escaped}'

# Adobe Reader 경로 확인
$acrord64Path = "C:\\Program Files (x86)\\Adobe\\Acrobat Reader DC\\Reader\\AcroRd32.exe"
$acrord32Path = "C:\\Program Files\\Adobe\\Acrobat DC\\Acrobat\\Acrobat.exe"
$acrord2024Path = "C:\\Program Files\\Adobe\\Acrobat Reader DC\\AcrobatReader.exe"

if (Test-Path $acrord64Path) {{
    # Adobe Reader의 /t 옵션: /t <파일경로> <프린터명>
    Start-Process -FilePath $acrord64Path -ArgumentList "/t", $pdfPath, $printerName -WindowStyle Hidden
    Write-Host "Adobe Reader로 프린터 $printerName 로 인쇄 시작"
    exit 0
}} elseif (Test-Path $acrord2024Path) {{
    Start-Process -FilePath $acrord2024Path -ArgumentList "/t", $pdfPath, $printerName -WindowStyle Hidden
    Write-Host "Adobe Reader로 프린터 $printerName 로 인쇄 시작"
    exit 0
}} elseif (Test-Path $acrord32Path) {{
    Start-Process -FilePath $acrord32Path -ArgumentList "/t", $pdfPath, $printerName -WindowStyle Hidden
    Write-Host "Adobe Reader로 프린터 $printerName 로 인쇄 시작"
    exit 0
}} else {{
    Write-Host "Adobe Reader를 찾을 수 없습니다. 기본 프린터 변경 방법 사용"
    exit 1
}}
'''
                
                result = subprocess.run([
                    'powershell', '-Command', ps_script
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    print(f"✅ Adobe Reader를 통해 프린터 '{printer_name}'로 PDF 인쇄 성공")
                    logger.info(f"프린터 '{printer_name}'로 PDF 인쇄 성공")
                    # Adobe Reader는 프린터를 직접 지정하므로 기본 프린터 복원 불필요
                    return True
                else:
                    print(f"⚠️ Adobe Reader 방법 실패: {result.stderr}")
                    print("대체 방법: 기본 프린터 임시 변경 후 인쇄...")
                    raise Exception("Adobe Reader 방법 실패")
                    
            except Exception as e:
                print(f"⚠️ Adobe Reader 방법 실패: {e}")
                
                # 방법 2: 기본 프린터 임시 변경 (폴백)
                try:
                    win32print.SetDefaultPrinter(printer_name)
                    print(f"✅ 기본 프린터를 '{printer_name}'로 임시 변경 성공")
                    
                    # 변경 확인 및 충분한 대기
                    import time
                    time.sleep(2)  # 프린터 변경이 시스템에 완전히 반영되도록 대기
                    
                    current_printer = win32print.GetDefaultPrinter()
                    print(f"⚠️ 인쇄 직전 기본 프린터 확인: {current_printer}")
                    
                    if current_printer != printer_name:
                        print(f"❌ 경고: 기본 프린터가 '{current_printer}'로 되어 있습니다!")
                        print(f"   예상된 프린터: '{printer_name}'")
                        # 다시 시도
                        win32print.SetDefaultPrinter(printer_name)
                        time.sleep(1)
                        current_printer = win32print.GetDefaultPrinter()
                    
                    if current_printer == printer_name:
                        print(f"✅ 확인: 기본 프린터가 '{printer_name}'로 정확히 설정되어 있습니다.")
                        os.startfile(pdf_path, 'print')
                        print(f"✅ PDF가 프린터로 전송되었습니다: {current_printer}")
                        
                        # 인쇄 완료 대기
                        time.sleep(5)
                        
                        # 원래 기본 프린터로 복원
                        try:
                            win32print.SetDefaultPrinter(original_default)
                            print(f"✅ 기본 프린터 복원 성공: {original_default}")
                        except Exception as e2:
                            print(f"⚠️ 기본 프린터 복원 실패: {e2}")
                        
                        logger.info(f"프린터 '{printer_name}'로 PDF 인쇄 성공")
                        return True
                    else:
                        print(f"❌ 기본 프린터 변경 실패. 현재 프린터: {current_printer}")
                        os.startfile(pdf_path, 'print')
                        return True
                        
                except Exception as e2:
                    print(f"❌ 기본 프린터 변경 방법도 실패: {e2}")
                    print("기본 프린터로 인쇄합니다.")
                    os.startfile(pdf_path, 'print')
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
        
        # 라벨 크기 설정 (TXT 파일에서 읽기)
        self.label_width_cm = 10.0  # 기본값
        self.label_height_cm = 5.0  # 기본값
        self.load_label_size_from_txt()
        
        # 폰트 설정 (TXT 파일에서 읽기)
        self.font_name = "Arial"  # 기본값
        self.font_size = 48  # 기본값
        self.load_font_from_txt()
        
        # 서버 IP 자동 감지
        self.server_ip = self.get_local_ip()
        self.server_port = self.find_available_port()
        
        # GUI 구성
        self.setup_gui()
        
        # 서버 시작
        self.start_server()
    
    def load_label_size_from_txt(self):
        """TXT 파일에서 라벨 크기 읽기"""
        try:
            config_file = "label_size.txt"
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if 'width' in line.lower() or '너비' in line:
                            try:
                                # "width: 12" 또는 "너비: 12" 형식 파싱
                                parts = line.split(':')
                                if len(parts) == 2:
                                    self.label_width_cm = float(parts[1].strip())
                            except:
                                pass
                        elif 'height' in line.lower() or '높이' in line:
                            try:
                                parts = line.split(':')
                                if len(parts) == 2:
                                    self.label_height_cm = float(parts[1].strip())
                            except:
                                pass
                        # 또는 "10,5" 형식으로 읽기
                        elif ',' in line:
                            try:
                                parts = line.split(',')
                                if len(parts) == 2:
                                    self.label_width_cm = float(parts[0].strip())
                                    self.label_height_cm = float(parts[1].strip())
                            except:
                                pass
                print(f"라벨 크기 설정 로드: {self.label_width_cm}cm x {self.label_height_cm}cm")
        except Exception as e:
            print(f"라벨 크기 설정 파일 읽기 실패: {e}, 기본값 사용")
    
    def load_font_from_txt(self):
        """TXT 파일에서 폰트 설정 읽기"""
        try:
            config_file = "label_size.txt"
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        # fontsize를 먼저 체크 (더 구체적인 조건)
                        if 'fontsize' in line.lower() or '폰트크기' in line or 'font_size' in line.lower():
                            try:
                                parts = line.split(':')
                                if len(parts) == 2:
                                    self.font_size = int(float(parts[1].strip()))
                            except:
                                pass
                        # font: 로 시작하는 줄만 체크 (fontsize 제외)
                        elif line.lower().startswith('font:') or line.startswith('폰트:'):
                            try:
                                parts = line.split(':')
                                if len(parts) == 2:
                                    self.font_name = parts[1].strip()
                            except:
                                pass
                print(f"폰트 설정 로드: {self.font_name} {self.font_size}pt")
        except Exception as e:
            print(f"폰트 설정 파일 읽기 실패: {e}, 기본값 사용")
    
    def on_font_changed(self, *args):
        """폰트 변경 시 미리보기 업데이트"""
        try:
            self.font_name = self.font_name_var.get() or "Arial"
            self.font_size = int(float(self.font_size_var.get() or "48"))
            if hasattr(self, 'label_canvas'):
                self.update_label_preview()
        except (ValueError, AttributeError):
            pass  # 잘못된 입력값 무시
    
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
        
        # 폰트 설정
        font_frame = ttk.Frame(form_frame)
        font_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(font_frame, text="폰트:").pack(side=tk.LEFT, padx=(0, 5))
        self.font_name_var = tk.StringVar(value=self.font_name)
        font_name_combo = ttk.Combobox(font_frame, textvariable=self.font_name_var, width=15, state="readonly")
        font_name_combo['values'] = ("Arial", "Helvetica", "Times New Roman", "Courier", "Georgia", "Verdana", "Comic Sans MS", "Impact")
        font_name_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.font_name_var.trace_add('write', self.on_font_changed)
        
        ttk.Label(font_frame, text="크기:").pack(side=tk.LEFT, padx=(0, 5))
        self.font_size_var = tk.StringVar(value=str(self.font_size))
        font_size_entry = ttk.Entry(font_frame, textvariable=self.font_size_var, width=8)
        font_size_entry.pack(side=tk.LEFT)
        self.font_size_var.trace_add('write', self.on_font_changed)
        
        # 프린터 선택
        ttk.Label(form_frame, text="프린터 선택:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.printer_var = tk.StringVar()
        self.printer_combo = ttk.Combobox(form_frame, textvariable=self.printer_var, state="readonly", width=27)
        self.printer_combo.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))
        
        # 라벨 미리보기 영역 추가
        self.setup_label_preview(form_frame)
    
    def setup_label_preview(self, parent):
        """라벨 미리보기 Canvas 설정"""
        preview_frame = ttk.LabelFrame(parent, text="라벨 미리보기", padding="10")
        preview_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Canvas 생성 (라벨 용지 사이즈에 맞게, 2배 크기로 미리보기)
        # 1cm = 37.8 pixels @ 96 DPI
        # 2배 미리보기: 1cm = 75.6 pixels
        # 라벨 용지 사이즈 기준으로 캔버스 크기 설정
        canvas_width = int(self.label_width_cm * 2 * 37.8)
        canvas_height = int(self.label_height_cm * 2 * 37.8)
        
        self.label_canvas = tk.Canvas(preview_frame, width=canvas_width, height=canvas_height, 
                                      bg="white", relief=tk.SUNKEN, borderwidth=2)
        self.label_canvas.pack()
        
        # 데이터 변경 시 미리보기 업데이트
        self.total_weight_var.trace_add('write', self.update_label_preview)
        self.pallet_weight_var.trace_add('write', self.update_label_preview)
        
        # 초기 미리보기 그리기
        self.update_label_preview()
    
    def update_label_preview(self, *args):
        """라벨 미리보기 업데이트 - 테두리와 정가운데 무게만, 좌측 하단에 바코드"""
        if not hasattr(self, 'label_canvas'):
            return
            
        canvas = self.label_canvas
        canvas.delete("all")
        
        # Canvas 실제 크기 가져오기 (라벨 용지 사이즈 기준)
        canvas.update_idletasks()
        # 라벨 용지 사이즈 기준 계산: 2배 미리보기
        base_canvas_width = int(self.label_width_cm * 2 * 37.8)  # 1cm = 75.6 pixels (2배)
        base_canvas_height = int(self.label_height_cm * 2 * 37.8)
        
        width = canvas.winfo_width() if canvas.winfo_width() > 1 else base_canvas_width
        height = canvas.winfo_height() if canvas.winfo_height() > 1 else base_canvas_height
        
        # Canvas 크기에 비례하여 폰트 크기 조정 (라벨 용지 사이즈 기준)
        base_font_size = self.font_size  # 설정된 폰트 크기 사용
        # 라벨 용지 사이즈 기준 비율 계산 (2배 미리보기 기준)
        scale = min(width / base_canvas_width, height / base_canvas_height)
        
        # 캔버스 시작 위치 오프셋 (테두리가 캔버스 가장자리에 바로 붙도록)
        offset_x = 0
        offset_y = 0
        
        # 배경 테두리 (캔버스 가장자리에 바로 그리기)
        border_width = max(2, int(2 * scale))  # 스케일에 맞게 테두리 두께 조정
        canvas.create_rectangle(0, 0, width, height, 
                                outline="black", width=border_width)
        
        try:
            # 데이터 가져오기
            total_weight = self.total_weight_var.get() or "0"
            pallet_weight = self.pallet_weight_var.get() or "0"
            net_weight = float(total_weight) - float(pallet_weight) if total_weight and pallet_weight else 0
            
            # 순수무게만 정가운데 크게 표시
            if net_weight > 0:
                # 중앙에 숫자만 크게 표시
                net_weight_number = f"{net_weight:.1f}"
                font_size = max(20, int(base_font_size * scale))
                
                # 설정된 폰트 이름 사용
                font_family = self.font_name if hasattr(self, 'font_name') else "Arial"
                
                # 중앙 위치 계산 (오프셋 고려)
                center_x = width / 2
                center_y = height / 2
                
                canvas.create_text(center_x, center_y, text=net_weight_number,
                                 font=(font_family, font_size, "bold"), fill="black")
                
                # 우측 하단에 "kg" 작게 표시
                kg_font_size = max(12, int(base_font_size * scale * 0.3))
                canvas.create_text(width - 10, height - 10, text="kg",
                                 font=(font_family, kg_font_size), fill="black", anchor="se")
                
                # 바코드: 순수무게를 바코드로 변환 (좌측 하단)
                # 무게 값을 바코드 문자열로 변환 (소수점 제거)
                barcode_value = f"{net_weight:.1f}".replace(".", "").zfill(6)  # 최소 6자리로 패딩
                
                # 실제 바코드 이미지 생성 시도
                try:
                    from barcode import Code128
                    from barcode.writer import ImageWriter
                    import io
                    
                    # 바코드 이미지 생성
                    barcode_image = Code128(barcode_value, writer=ImageWriter())
                    barcode_buffer = io.BytesIO()
                    barcode_image.write(barcode_buffer)
                    barcode_buffer.seek(0)
                    
                    # PIL Image로 변환
                    from PIL import Image as PILImage
                    barcode_pil = PILImage.open(barcode_buffer)
                    
                    # 바코드 크기 조정 (좌측 하단에 배치) - 사이즈 키움
                    barcode_height = int(height * 0.25)  # 높이의 25% (15% → 25%로 증가)
                    barcode_aspect = barcode_pil.width / barcode_pil.height
                    barcode_width = int(barcode_height * barcode_aspect)
                    barcode_resized = barcode_pil.resize((barcode_width, barcode_height), PILImage.Resampling.LANCZOS)
                    
                    # Canvas에 바코드 이미지 추가 (좌측 하단)
                    from PIL import ImageTk
                    barcode_tk = ImageTk.PhotoImage(barcode_resized)
                    canvas.create_image(10, height - int(barcode_height/2) - 10, 
                                       anchor="sw", image=barcode_tk)
                    canvas.barcode_image = barcode_tk  # 참조 유지
                    
                except ImportError:
                    # barcode 라이브러리가 없으면 텍스트로 표시
                    barcode_font_size = max(10, int(12 * scale))
                    canvas.create_text(10, height - 10, text=barcode_value,
                                     anchor="w", font=("Arial", barcode_font_size), fill="black")
                except Exception as e:
                    # 바코드 생성 실패 시 텍스트로 표시
                    print(f"바코드 생성 실패: {e}")
                    barcode_font_size = max(10, int(12 * scale))
                    canvas.create_text(10, height - 10, text=barcode_value,
                                     anchor="w", font=("Arial", barcode_font_size), fill="black")
        except Exception as e:
            print(f"미리보기 업데이트 오류: {e}")
            pass  # 데이터가 없으면 그냥 빈 캔버스
    
    def setup_buttons(self, parent):
        """버튼들"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="라벨 인쇄", command=self.print_label).pack(side=tk.LEFT, padx=5)
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
                self.net_weight_var.set(f"{net_weight:.1f} kg")
            else:
                self.net_weight_var.set("0.0 kg")
        except ValueError:
            self.net_weight_var.set("0.0 kg")
    
    def reset_form(self):
        """폼 초기화"""
        self.total_weight_var.set("")
        self.pallet_weight_var.set("")
        self.net_weight_var.set("0.0 kg")
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
            'net_weight': f"{net_weight:.1f}",
            'weight': f"{net_weight:.1f}",  # 라벨에 표시될 무게 (순수무게)
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
        """라벨 인쇄 - Canvas를 이미지로 캡처하여 직접 인쇄"""
        data = self.get_label_data()
        
        if not self.validate_data(data):
            return
            
        try:
            # Canvas 미리보기 업데이트 (최신 데이터 반영)
            self.update_label_preview()
            
            # 실제 프린터 이름 가져오기
            display_name = data['printer']
            actual_printer_name = self.printer_names.get(display_name, None)
            
            if not actual_printer_name:
                messagebox.showerror("오류", "프린터를 선택해주세요.")
                return
            
            print(f"선택된 프린터: {actual_printer_name}")
            
            # 라벨 용지 사이즈에 맞게 PIL Image로 직접 생성 (고정 크기, 화면 해상도 무관)
            from PIL import Image, ImageDraw, ImageFont
            import tempfile
            
            # 임시 파일 경로 생성
            temp_canvas_path = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            temp_img_path = temp_canvas_path.name
            temp_canvas_path.close()
            
            # 300 DPI 기준으로 라벨 용지 사이즈에 맞는 절대적인 크기 계산
            # 1cm = 118.11 pixels @ 300 DPI
            target_width = int(self.label_width_cm * 118.11)  # 300 DPI 기준
            target_height = int(self.label_height_cm * 118.11)
            
            print(f"라벨 용지 사이즈: {self.label_width_cm}cm x {self.label_height_cm}cm")
            print(f"인쇄 목표 크기 (300 DPI): {target_width} x {target_height} 픽셀")
            
            # PIL Image 생성 (화이트 배경)
            img = Image.new('RGB', (target_width, target_height), 'white')
            draw = ImageDraw.Draw(img)
            
            # 데이터 가져오기
            total_weight = data['total_weight'] or "0"
            pallet_weight = data['pallet_weight'] or "0"
            net_weight = float(total_weight) - float(pallet_weight) if total_weight and pallet_weight else 0
            
            # 테두리가 이미지 가장자리에 바로 붙도록 오프셋 제거
            offset_px = 0
            
            if net_weight > 0:
                # 1. 테두리 그리기 (이미지 가장자리에 바로)
                border_width = 3
                draw.rectangle([0, 0, target_width, target_height], 
                             outline='black', width=border_width)
                
                # 2. 중앙에 숫자 그리기 (캔버스 미리보기와 동일한 비율로 계산)
                net_weight_number = f"{net_weight:.1f}"
                
                # 캔버스 미리보기와 동일한 폰트 크기 계산 방식 사용
                # 캔버스: 2배 미리보기 기준 (96 DPI)
                # - base_canvas_width = label_width_cm * 2 * 37.8
                # - scale = width / base_canvas_width
                # - font_size = base_font_size * scale
                #
                # 인쇄: 300 DPI 기준
                # - target_width = label_width_cm * 118.11 (300 DPI)
                # - 캔버스와 동일한 비율을 적용하기 위해:
                #   canvas_scale = target_width / (label_width_cm * 2 * 37.8 * 2)
                #   실제로는 300 DPI에서의 실제 크기로 조정
                
                base_font_size = self.font_size
                
                # 캔버스 미리보기 기준 계산
                # 캔버스는 2배 스케일 미리보기: base_canvas_width = label_width_cm * 2 * 37.8
                # 실제 인쇄 크기는: target_width = label_width_cm * 118.11
                # 비율: target_width / (label_width_cm * 2 * 37.8) = 118.11 / (2 * 37.8) ≈ 1.56
                
                # 하지만 더 정확하게는, 캔버스에서 사용하는 폰트 크기와 동일한 비율로 맞추기
                # 캔버스에서: font_size = base_font_size * scale (scale은 캔버스 크기 비율)
                # 인쇄에서도 동일한 비율 적용
                
                # 캔버스 기준 너비 (2배 미리보기): label_width_cm * 2 * 37.8
                canvas_base_width = self.label_width_cm * 2 * 37.8
                # 인쇄 크기 대비 캔버스 크기 비율
                scale_ratio = target_width / canvas_base_width
                
                # 캔버스에서 사용하는 폰트 크기 계산 방식 적용
                # 캔버스에서 scale은 실제 캔버스 크기 / base_canvas_width
                # 인쇄에서는 동일한 비율 적용
                font_size = int(base_font_size * scale_ratio)
                font_size = max(20, font_size)  # 최소 크기 보장
                
                # 폰트 로드 시도 (설정된 폰트 이름 사용, 볼드 버전)
                # 캔버스에서는 "bold" 스타일을 사용하므로, PIL에서도 볼드 폰트 파일 사용
                font_name = self.font_name if hasattr(self, 'font_name') else "Arial"
                
                # 폰트 파일 매핑 (볼드 버전 포함)
                font_file_map = {
                    "Arial": "arialbd.ttf",  # bold 버전
                    "Times New Roman": "timesbd.ttf",  # bold 버전
                    "Courier": "courbd.ttf",  # bold 버전
                    "Georgia": "georgiab.ttf",  # bold 버전 (있다면)
                    "Verdana": "verdanab.ttf",  # bold 버전 (있다면)
                    "Helvetica": "arialbd.ttf",  # Helvetica는 Arial로 대체
                }
                
                # 일반 버전 매핑 (볼드가 없을 경우 대체)
                font_file_map_normal = {
                    "Arial": "arial.ttf",
                    "Times New Roman": "times.ttf",
                    "Courier": "cour.ttf",
                    "Georgia": "georgia.ttf",
                    "Verdana": "verdana.ttf",
                    "Helvetica": "arial.ttf",
                }
                
                # 볼드 폰트 파일 우선 시도
                font_file = font_file_map.get(font_name, "arialbd.ttf")
                font_paths = [
                    f"C:/Windows/Fonts/{font_file}",
                    f"C:/Windows/Fonts/{font_file_map_normal.get(font_name, 'arial.ttf')}",  # 일반 버전 fallback
                    "C:/Windows/Fonts/arialbd.ttf",  # 최종 fallback
                    "C:/Windows/Fonts/arial.ttf",
                ]
                
                font = None
                for font_path in font_paths:
                    try:
                        if os.path.exists(font_path):
                            font = ImageFont.truetype(font_path, font_size)
                            print(f"폰트 로드 성공: {font_path}, 크기: {font_size}")
                            break
                    except Exception as e:
                        continue
                
                if font is None:
                    print("⚠️ 폰트 로드 실패, 기본 폰트 사용")
                    font = ImageFont.load_default()
                
                # 텍스트 크기 측정 및 정확한 중앙 정렬
                # textbbox는 (left, top, right, bottom) 반환
                # top은 음수일 수 있음 (기준선 위쪽 여백)
                # PIL의 text() 메서드는 y 좌표를 기준선(baseline)으로 사용
                
                # 텍스트 바운딩 박스 측정 (기준선을 0으로 가정)
                bbox = draw.textbbox((0, 0), net_weight_number, font=font)
                
                # bbox: (left, top, right, bottom)
                # top은 기준선 위쪽 거리 (보통 음수)
                # bottom은 기준선 아래쪽 거리 (보통 양수)
                left, top, right, bottom = bbox
                
                text_width = right - left
                text_height = bottom - top  # 전체 높이 (위쪽 + 아래쪽)
                
                # 기준선(baseline)에서 텍스트 중앙까지의 거리
                # top이 음수이므로, 중앙은 (top + bottom) / 2
                text_center_from_baseline = (top + bottom) / 2
                
                # 중앙 위치
                center_x = target_width / 2
                center_y = target_height / 2
                
                # 텍스트를 정확히 중앙에 배치
                # baseline_y = center_y - text_center_from_baseline
                text_x = center_x - text_width / 2
                text_y = center_y - text_center_from_baseline
                
                # 숫자 그리기 (정확한 중앙 정렬)
                draw.text((text_x, text_y), net_weight_number, fill='black', font=font)
                
                # 3. 우측 하단에 "kg" 작게 표시
                kg_font_size = int(font_size * 0.3)
                try:
                    kg_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", kg_font_size)
                except:
                    kg_font = ImageFont.load_default()
                
                kg_bbox = draw.textbbox((0, 0), "kg", font=kg_font)
                kg_width = kg_bbox[2] - kg_bbox[0]
                kg_height = kg_bbox[3] - kg_bbox[1]
                
                draw.text((target_width - 10 - kg_width, 
                          target_height - 10 - kg_height), 
                         "kg", fill='black', font=kg_font)
                
                # 4. 바코드: 좌측 하단 (라벨 용지 사이즈에 비례한 절대적인 크기)
                barcode_value = f"{net_weight:.1f}".replace(".", "").zfill(6)
                
                try:
                    from barcode import Code128
                    from barcode.writer import ImageWriter
                    import io
                    
                    # 바코드 이미지 생성
                    barcode_image = Code128(barcode_value, writer=ImageWriter())
                    barcode_buffer = io.BytesIO()
                    barcode_image.write(barcode_buffer)
                    barcode_buffer.seek(0)
                    
                    # PIL Image로 변환
                    from PIL import Image as PILImage
                    barcode_pil = PILImage.open(barcode_buffer)
                    
                    # 바코드 크기 조정 (라벨 높이의 25%)
                    barcode_height = int(target_height * 0.25)
                    barcode_aspect = barcode_pil.width / barcode_pil.height
                    barcode_width = int(barcode_height * barcode_aspect)
                    barcode_resized = barcode_pil.resize((barcode_width, barcode_height), 
                                                        PILImage.Resampling.LANCZOS)
                    
                    # 바코드를 좌측 하단에 배치
                    barcode_x = 10
                    barcode_y = target_height - 10 - barcode_height
                    
                    img.paste(barcode_resized, (barcode_x, barcode_y))
                    
                except Exception as e:
                    # 바코드 생성 실패 시 텍스트로 표시
                    print(f"바코드 생성 실패: {e}")
                    barcode_font_size = int(target_height * 0.05)
                    try:
                        barcode_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", barcode_font_size)
                    except:
                        barcode_font = ImageFont.load_default()
                    
                    draw.text((10, target_height - 10), 
                             barcode_value, fill='black', font=barcode_font)
            
            # 이미지 저장 (300 DPI)
            img.save(temp_img_path, 'PNG', dpi=(300, 300))
            print(f"✅ PIL Image 직접 생성 완료: {target_width} x {target_height} 픽셀 (300 DPI)")
            print(f"이미지 파일: {temp_img_path}")
            
            # 이미지를 프린터로 직접 전송 (Word/한글 방식)
            # 라벨용지 사이즈 전달하여 정확한 크기로 인쇄
            success = self.printer.print_image(temp_img_path, actual_printer_name, 
                                               label_width_cm=self.label_width_cm, 
                                               label_height_cm=self.label_height_cm)
            
            # 임시 파일 삭제
            try:
                os.remove(temp_ps_path)
            except:
                pass
            try:
                os.remove(temp_img_path)
            except:
                pass
            
            if success:
                # 인쇄 기록 저장
                self.save_print_record(data)
                messagebox.showinfo("성공", f"프린터 '{actual_printer_name}'로 라벨이 성공적으로 인쇄되었습니다.")
            else:
                messagebox.showerror("오류", "인쇄에 실패했습니다. 프린터 설정을 확인해주세요.")
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("오류", f"인쇄 중 오류가 발생했습니다: {str(e)}")
            
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
                
                except Exception as e:
                    print(f"Windows 프린터 조회 오류: {e}")
                    printer_list.append("기본 프린터")
                    self.printer_names["기본 프린터"] = None

                # 프린터가 없으면 기본 프린터 추가
                if not printer_list:
                    printer_list.append("기본 프린터")
                    self.printer_names["기본 프린터"] = None
                
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
                data['net_weight'] = f"{net_weight:.1f}"
                data['weight'] = f"{net_weight:.1f}"  # 라벨에 표시될 무게
                if not data.get('date'):
                    data['date'] = datetime.now().strftime('%Y-%m-%d')
                if not data.get('product_name'):
                    data['product_name'] = '제품'
                if not data.get('printer'):
                    data['printer'] = '기본 프린터'
                
                # 실제 프린터 이름 가져오기
                display_name = data.get('printer', '기본 프린터')
                
                # API에서는 프린터 이름을 직접 사용 (GUI의 매핑 없이)
                if display_name == '기본 프린터' or display_name == 'default':
                    actual_printer_name = None  # 기본 프린터 사용
                else:
                    actual_printer_name = display_name  # 프린터 이름 직접 사용
                
                print(f"API 인쇄 - 선택된 프린터: {display_name}")
                print(f"API 인쇄 - 실제 프린터명: {actual_printer_name}")
                
                # 이미지 직접 생성 방식으로 인쇄 (GUI와 동일)
                from PIL import Image, ImageDraw, ImageFont
                import tempfile
                
                # 임시 파일 경로 생성
                temp_img_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                temp_img_path = temp_img_file.name
                temp_img_file.close()
                
                # 300 DPI 기준으로 라벨 용지 사이즈에 맞는 절대적인 크기 계산
                target_width = int(self.label_width_cm * 118.11)  # 300 DPI 기준
                target_height = int(self.label_height_cm * 118.11)
                
                print(f"API 인쇄 - 라벨 용지 사이즈: {self.label_width_cm}cm x {self.label_height_cm}cm")
                print(f"API 인쇄 - 목표 크기 (300 DPI): {target_width} x {target_height} 픽셀")
                
                # PIL Image 생성 (화이트 배경)
                img = Image.new('RGB', (target_width, target_height), 'white')
                draw = ImageDraw.Draw(img)
                
                # 순수무게 사용
                total_weight_str = data.get('total_weight', '0')
                pallet_weight_str = data.get('pallet_weight', '0')
                net_weight = float(total_weight_str) - float(pallet_weight_str) if total_weight_str and pallet_weight_str else 0
                
                if net_weight > 0:
                    # 1. 테두리 그리기
                    border_width = 3
                    draw.rectangle([0, 0, target_width, target_height], 
                                 outline='black', width=border_width)
                    
                    # 2. 중앙에 숫자 그리기
                    net_weight_number = f"{net_weight:.1f}"
                    
                    # 폰트 크기 계산 (GUI와 동일한 방식)
                    base_font_size = self.font_size
                    canvas_base_width = self.label_width_cm * 2 * 37.8
                    scale_ratio = target_width / canvas_base_width
                    font_size = int(base_font_size * scale_ratio)
                    font_size = max(20, font_size)
                    
                    # 폰트 로드
                    font_name = self.font_name if hasattr(self, 'font_name') else "Arial"
                    font_file_map = {
                        "Arial": "arialbd.ttf",
                        "Times New Roman": "timesbd.ttf",
                        "Courier": "courbd.ttf",
                        "Georgia": "georgiab.ttf",
                        "Verdana": "verdanab.ttf",
                        "Helvetica": "arialbd.ttf",
                    }
                    font_file_map_normal = {
                        "Arial": "arial.ttf",
                        "Times New Roman": "times.ttf",
                        "Courier": "cour.ttf",
                        "Georgia": "georgia.ttf",
                        "Verdana": "verdana.ttf",
                        "Helvetica": "arial.ttf",
                    }
                    
                    font_file = font_file_map.get(font_name, "arialbd.ttf")
                    font_paths = [
                        f"C:/Windows/Fonts/{font_file}",
                        f"C:/Windows/Fonts/{font_file_map_normal.get(font_name, 'arial.ttf')}",
                        "C:/Windows/Fonts/arialbd.ttf",
                        "C:/Windows/Fonts/arial.ttf",
                    ]
                    
                    font = None
                    for font_path in font_paths:
                        try:
                            if os.path.exists(font_path):
                                font = ImageFont.truetype(font_path, font_size)
                                break
                        except:
                            continue
                    
                    if font is None:
                        font = ImageFont.load_default()
                    
                    # 텍스트 중앙 정렬
                    bbox = draw.textbbox((0, 0), net_weight_number, font=font)
                    left, top, right, bottom = bbox
                    text_width = right - left
                    text_center_from_baseline = (top + bottom) / 2
                    
                    center_x = target_width / 2
                    center_y = target_height / 2
                    text_x = center_x - text_width / 2
                    text_y = center_y - text_center_from_baseline
                    
                    draw.text((text_x, text_y), net_weight_number, fill='black', font=font)
                    
                    # 3. 우측 하단에 "kg" 표시
                    kg_font_size = int(font_size * 0.3)
                    try:
                        kg_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", kg_font_size)
                    except:
                        kg_font = ImageFont.load_default()
                    
                    kg_bbox = draw.textbbox((0, 0), "kg", font=kg_font)
                    kg_width = kg_bbox[2] - kg_bbox[0]
                    kg_height = kg_bbox[3] - kg_bbox[1]
                    
                    draw.text((target_width - 10 - kg_width, 
                              target_height - 10 - kg_height), 
                             "kg", fill='black', font=kg_font)
                    
                    # 4. 바코드: 좌측 하단
                    barcode_value = f"{net_weight:.1f}".replace(".", "").zfill(6)
                    
                    try:
                        from barcode import Code128
                        from barcode.writer import ImageWriter
                        import io
                        
                        barcode_image = Code128(barcode_value, writer=ImageWriter())
                        barcode_buffer = io.BytesIO()
                        barcode_image.write(barcode_buffer)
                        barcode_buffer.seek(0)
                        
                        from PIL import Image as PILImage
                        barcode_pil = PILImage.open(barcode_buffer)
                        
                        barcode_height = int(target_height * 0.25)
                        barcode_aspect = barcode_pil.width / barcode_pil.height
                        barcode_width = int(barcode_height * barcode_aspect)
                        barcode_resized = barcode_pil.resize((barcode_width, barcode_height), 
                                                            PILImage.Resampling.LANCZOS)
                        
                        barcode_x = 10
                        barcode_y = target_height - 10 - barcode_height
                        img.paste(barcode_resized, (barcode_x, barcode_y))
                        
                    except Exception as e:
                        print(f"바코드 생성 실패: {e}")
                        barcode_font_size = int(target_height * 0.05)
                        try:
                            barcode_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", barcode_font_size)
                        except:
                            barcode_font = ImageFont.load_default()
                        
                        draw.text((10, target_height - 10), 
                                 barcode_value, fill='black', font=barcode_font)
                
                # 이미지 저장 (300 DPI)
                img.save(temp_img_path, 'PNG', dpi=(300, 300))
                print(f"✅ API 인쇄 - PIL Image 생성 완료: {target_width} x {target_height} 픽셀 (300 DPI)")
                
                # 이미지를 프린터로 직접 전송 (Word/한글 방식)
                success = self.printer.print_image(temp_img_path, actual_printer_name, 
                                                   label_width_cm=self.label_width_cm, 
                                                   label_height_cm=self.label_height_cm)
                
                # 임시 파일 삭제
                try:
                    os.remove(temp_img_path)
                except:
                    pass
                
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
