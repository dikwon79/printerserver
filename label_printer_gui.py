import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import webbrowser
from datetime import datetime
import os
import tempfile
import subprocess
import socket
import json
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
BULK_SHEET_PAGE_SIZE = A4

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
    
    def create_bulk_production_sheet_pdf(self, data=None):
        """벌크 생산 시트 PDF 생성"""
        data = data or {}
        pdf_path = os.path.join(self.temp_dir, f"bulk_sheet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        
        c = canvas.Canvas(pdf_path, pagesize=BULK_SHEET_PAGE_SIZE)
        page_width, page_height = BULK_SHEET_PAGE_SIZE
        margin = 1.0 * cm
        
        # Header table - 3 columns (left: 20%, center: 45%, right: 35%)
        header_height = 1.6 * cm
        header_top = page_height - 0.8 * cm
        header_bottom = header_top - header_height
        header_width = page_width - 2 * margin
        left_col_width = header_width * 0.25
        center_col_width = header_width * 0.40
        right_col_width = header_width * 0.35
        
        # Draw header table borders
        c.rect(margin, header_bottom, header_width, header_height)
        c.line(margin + left_col_width, header_bottom, margin + left_col_width, header_top)
        c.line(margin + left_col_width + center_col_width, header_bottom, margin + left_col_width + center_col_width, header_top)
        
        # Left cell - innofoods INC
        header_center_y = header_bottom + header_height / 2
        c.setFont("Helvetica-Bold", 22)
        c.setFillColorRGB(0.0, 0.4, 0.6)
        logo_text = "innofoods"
        logo_x = margin + 0.3 * cm  # 왼쪽으로 이동
        c.drawString(logo_x, header_center_y - 0.3 * cm, logo_text)
        c.setFont("Helvetica-Bold", 7)  # INC를 더 작게
        inc_text = "INC"
        logo_width = c.stringWidth(logo_text, "Helvetica-Bold", 22)
        inc_x = logo_x + logo_width + 0.2 * cm
        c.drawString(inc_x, header_center_y - 0.5 * cm, inc_text)  # 아래로 이동
       
        
        # Center cell - Daily Bulk Production Sheet
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 14)  # 폰트 크기 줄임
        title_text = "Daily Bulk Production Sheet"
        title_width = c.stringWidth(title_text, "Helvetica-Bold", 14)
        center_start_x = margin + left_col_width
        title_x = center_start_x + (center_col_width - title_width) / 2
        c.drawString(title_x, header_center_y - 0.2 * cm, title_text)
        
        # Right cell - Document info
        c.setFont("Helvetica", 9)
        doc_info = [
            ("Document No.:", data.get("document_no", "INNO-PROU-PUT-LUS")),
            ("Issue No.:", data.get("issue_no", "014")),
            ("Effective Date:", data.get("effective_date", "Sep 14, 2023")),
            ("Issued By:", data.get("issued_by", "Jason Lee")),
            ("Approved By:", data.get("approved_by", "Jeff Chen")),
            ("Review Date:", data.get("review_date", "Sep 14, 2023")),
        ]
        right_start_x = margin + left_col_width + center_col_width
        doc_start_x = right_start_x + 0.2 * cm
        line_spacing = 0.25 * cm  # 줄 간격 증가
        doc_start_y = header_top - 0.3 * cm
        for idx, (label, value) in enumerate(doc_info):
            y_pos = doc_start_y - idx * line_spacing
            c.drawString(doc_start_x, y_pos, label)
            c.drawString(doc_start_x + 2.2 * cm, y_pos, value)
        
        # Form table - each row is a separate cell with borders
        form_top = header_bottom - 0.3 * cm
        form_width = page_width - 2 * margin
        row_height = 1.0 * cm
        left_col_width = form_width * 0.5
        right_col_width = form_width * 0.5
        
        c.setFont("Helvetica", 11)
        
        # Helper function to draw vertically centered text in cell
        def draw_centered_text(x, y_bottom, height, text, font_size=11):
            center_y = y_bottom + height / 2
            c.setFont("Helvetica", font_size)
            c.drawString(x, center_y - 0.2 * cm, text)
        
        # Row 1: DATE (left) and SHIFT (right)
        row1_y = form_top
        row1_bottom = row1_y - row_height
        # Left cell - DATE
        c.rect(margin, row1_bottom, left_col_width, row_height)
        draw_centered_text(margin + 0.15 * cm, row1_bottom, row_height, "DATE:")
        date_value = data.get("date", "")
        if date_value:
            draw_centered_text(margin + 1.8 * cm, row1_bottom, row_height, date_value)
        # Right cell - SHIFT
        c.rect(margin + left_col_width, row1_bottom, right_col_width, row_height)
        draw_centered_text(margin + left_col_width + 0.15 * cm, row1_bottom, row_height, "SHIFT (circle one):")
        c.setFont("Helvetica", 9)
        shift_center_y = row1_bottom + row_height / 2
        c.drawString(margin + left_col_width + 3.8 * cm, shift_center_y - 0.2 * cm, "AM / PM / Graveyard")
        shift_value = data.get("shift", "").upper()
        if shift_value:
            # AM 위치를 기준으로 선택값에 따라 타원형 원 그리기
            base_x = margin + left_col_width + 3.8 * cm  # 기준 위치
            if shift_value == "AM":
                ellipse_center_x = base_x + 0.2 * cm  # AM은 0.2cm 오른쪽
            elif shift_value == "PM":
                ellipse_center_x = base_x + 0.9 * cm  # PM은 0.7cm 오른쪽 (0.3cm 추가 이동)
            elif shift_value == "GRAVEYARD" or shift_value.startswith("G"):
                ellipse_center_x = base_x + 1.8 * cm  # GRAVEYARD는 4cm 오른쪽
            else:
                ellipse_center_x = base_x + 0.2 * cm
            
            # 타원형 원 그리기 (오른쪽으로 늘린 형태)
            ellipse_width = 0.8 * cm  # 가로 너비
            ellipse_height = 0.3 * cm  # 세로 높이
            ellipse_x1 = ellipse_center_x - ellipse_width / 2
            ellipse_y1 = shift_center_y - ellipse_height / 2
            ellipse_x2 = ellipse_center_x + ellipse_width / 2
            ellipse_y2 = shift_center_y + ellipse_height / 2
            c.ellipse(ellipse_x1, ellipse_y1, ellipse_x2, ellipse_y2)
        
        # Row 2: Supervisor Name (left) and Employee Name (right)
        row2_y = row1_y - row_height
        row2_bottom = row2_y - row_height
        c.setFont("Helvetica", 11)
        # Left cell
        c.rect(margin, row2_bottom, left_col_width, row_height)
        supervisor_label = "Supervisor Name:"
        supervisor_label_x = margin + 0.15 * cm
        draw_centered_text(supervisor_label_x, row2_bottom, row_height, supervisor_label)
        supervisor_value = data.get("supervisor_name", "")
        if supervisor_value:
            # 타이틀 끝에서 여백 추가
            supervisor_label_width = c.stringWidth(supervisor_label, "Helvetica", 11)
            supervisor_value_x = supervisor_label_x + supervisor_label_width + 0.3 * cm
            draw_centered_text(supervisor_value_x, row2_bottom, row_height, supervisor_value)
        # Right cell
        c.rect(margin + left_col_width, row2_bottom, right_col_width, row_height)
        employee_label = "Employee Name:"
        employee_label_x = margin + left_col_width + 0.15 * cm
        draw_centered_text(employee_label_x, row2_bottom, row_height, employee_label)
        employee_value = data.get("employee_name", "")
        if employee_value:
            # 타이틀 끝에서 여백 추가
            employee_label_width = c.stringWidth(employee_label, "Helvetica", 11)
            employee_value_x = employee_label_x + employee_label_width + 0.3 * cm
            draw_centered_text(employee_value_x, row2_bottom, row_height, employee_value)
        
        # Row 3: Product Name (left) and Bulk Lot Code (right)
        row3_y = row2_y - row_height
        row3_bottom = row3_y - row_height
        # Left cell
        c.rect(margin, row3_bottom, left_col_width, row_height)
        draw_centered_text(margin + 0.15 * cm, row3_bottom, row_height, "Product Name:")
        product_value = data.get("product_name", "")
        if product_value:
            draw_centered_text(margin + 2.8 * cm, row3_bottom, row_height, product_value)
        # Right cell
        c.rect(margin + left_col_width, row3_bottom, right_col_width, row_height)
        draw_centered_text(margin + left_col_width + 0.15 * cm, row3_bottom, row_height, "Bulk Lot Code:")
        bulk_lot_value = data.get("bulk_lot_code", "")
        if bulk_lot_value:
            draw_centered_text(margin + left_col_width + 2.8 * cm, row3_bottom, row_height, bulk_lot_value)
        
        # Row 4: Parchment Paper and Quantity (full width)
        row4_y = row3_y - row_height
        row4_bottom = row4_y - row_height
        # Full width cell
        c.rect(margin, row4_bottom, form_width, row_height)
        row4_center_y = row4_bottom + row_height / 2 + 0.27 * cm  # 콘텐츠를 위로 이동
        
        # Parchment Paper: REUSE
        c.drawString(margin + 0.15 * cm, row4_center_y - 0.2 * cm, "Parchment Paper: Reuse")
        reuse_text_width = c.stringWidth("Parchment Paper: Reuse", "Helvetica", 11)
        
        # 두 개 겹친 네모박스 (중심 같고 크기만 다름)
        checkbox_center_x = margin + reuse_text_width + 0.2 * cm + 0.2 * cm  # REUSE 텍스트 끝 + 여백 + 박스 중심
        checkbox_center_y = row4_center_y
        
        # 첫 번째 네모박스 (큰 것)
        checkbox_size1 = 0.4 * cm
        checkbox1_x = checkbox_center_x - checkbox_size1 / 2
        checkbox1_y = checkbox_center_y - checkbox_size1 / 2
        c.rect(checkbox1_x, checkbox1_y, checkbox_size1, checkbox_size1)
        
        # 두 번째 네모박스 (작은 것, 같은 중심)
        checkbox_size2 = 0.25 * cm
        checkbox2_x = checkbox_center_x - checkbox_size2 / 2
        checkbox2_y = checkbox_center_y - checkbox_size2 / 2
        c.rect(checkbox2_x, checkbox2_y, checkbox_size2, checkbox_size2)
        
        if data.get("parchment_reuse"):
            # 체크 표시 (큰 박스에만)
            c.line(checkbox1_x, checkbox1_y, checkbox1_x + checkbox_size1, checkbox1_y + checkbox_size1)
            c.line(checkbox1_x, checkbox1_y + checkbox_size1, checkbox1_x + checkbox_size1, checkbox1_y)
        
        # or Lot code: 밑줄 있는 입력 폼
        lot_code_label = "or Lot code:"
        lot_code_label_x = checkbox_center_x + checkbox_size1 / 2 + 0.3 * cm
        c.drawString(lot_code_label_x, row4_center_y - 0.2 * cm, lot_code_label)
        lot_code_label_width = c.stringWidth(lot_code_label, "Helvetica", 11)
        lot_code_line_x = lot_code_label_x + lot_code_label_width + 0.2 * cm
        lot_code_line_width = 4.0 * cm
        lot_code_line_y = row4_center_y - 0.3 * cm
        c.line(lot_code_line_x, lot_code_line_y, lot_code_line_x + lot_code_line_width, lot_code_line_y)
        lot_code_value = data.get("parchment_lot_code", "")
        if lot_code_value:
            c.drawString(lot_code_line_x + 0.1 * cm, lot_code_line_y + 0.1 * cm, lot_code_value)
        
        # 체크되면 parchment 라인 위에 텍스트 표시 (3cm 오른쪽으로 이동)
        if data.get("no_choco_coating"):
            choco_text = "No need for choco coating"
            choco_text_y = lot_code_line_y - 0.4 * cm  # 라인 위에 표기
            choco_text_x = lot_code_line_x + 3.0 * cm  # 3cm 오른쪽으로 이동
            c.drawString(choco_text_x, choco_text_y, choco_text)
        
        # Quantity: 오른쪽에 밑줄 있는 입력줄
        quantity_label = "Quantity:"
        quantity_label_width = c.stringWidth(quantity_label, "Helvetica", 11)
        quantity_label_x = page_width - margin - 5.0 * cm - quantity_label_width
        c.drawString(quantity_label_x, row4_center_y - 0.2 * cm, quantity_label)
        quantity_line_x = quantity_label_x + quantity_label_width + 0.2 * cm
        quantity_line_width = 4.0 * cm
        quantity_line_y = row4_center_y - 0.3 * cm
        c.line(quantity_line_x, quantity_line_y, quantity_line_x + quantity_line_width, quantity_line_y)
        quantity_value = data.get("quantity", "")
        if quantity_value:
            c.drawString(quantity_line_x + 0.1 * cm, quantity_line_y + 0.1 * cm, quantity_value)
        
        # Row 5: Quality Checked (full width)
        qc_y = row4_y - row_height
        qc_bottom = qc_y - row_height
        c.rect(margin, qc_bottom, form_width, row_height)
        qc_center_y = qc_bottom + row_height / 2
        c.drawString(margin + 0.15 * cm, qc_center_y - 0.2 * cm, "Quality Checked (e.g. color, texture, crumb, taste) - Supervisor Initial:")
        quality_value = data.get("quality_checked", "")
        if quality_value:
            qc_initial_x = page_width - margin - c.stringWidth(quality_value, "Helvetica", 11) - 0.15 * cm
            c.drawString(qc_initial_x, qc_center_y - 0.2 * cm, quality_value)
        
        # Thick line separator after Quality Checked
        c.setLineWidth(2)
        separator_y = qc_bottom - 0.2 * cm
        c.line(margin, separator_y, page_width - margin, separator_y)
        c.setLineWidth(1)
        
        # Main table
        table_top = separator_y - 0.3 * cm
        table_left = margin
        table_width = page_width - 2 * margin
        table_header_height = 1.1 * cm
        body_row_height = 1.0 * cm
        body_rows = 15
        table_height = table_header_height + body_rows * body_row_height
        table_bottom = table_top - table_height
        
        c.rect(table_left, table_bottom, table_width, table_height)
        
        column_specs = [
            ("Bulk Plastic Bag \nLot Codes", 0.28),
            ("Bulk Bag \nQTY", 0.14),
            ("Pallet #", 0.13),
            ("Total KG", 0.13),
            ("Notes", 0.24),
            ("Initial", 0.08),
        ]
        
        x_positions = [table_left]
        for _, ratio in column_specs:
            x_positions.append(x_positions[-1] + ratio * table_width)
        for x in x_positions[1:-1]:
            c.line(x, table_bottom, x, table_top)
        c.line(table_left, table_top - table_header_height, table_left + table_width, table_top - table_header_height)
        
        # Header row - vertically centered
        c.setFont("Helvetica-Bold", 11)
        header_center_y = table_top - table_header_height / 2
        for idx, (title, _) in enumerate(column_specs):
            text_x = x_positions[idx] + 0.3 * cm
            # 줄바꿈 처리
            if '\n' in title:
                lines = title.split('\n')
                line_height = 0.4 * cm
                total_height = len(lines) * line_height
                start_y = header_center_y + total_height / 2 - line_height / 2
                for line_idx, line in enumerate(lines):
                    y_pos = start_y - line_idx * line_height
                    c.drawString(text_x, y_pos - 0.1 * cm, line)
            else:
                c.drawString(text_x, header_center_y - 0.2 * cm, title)
        
        # Body rows - draw horizontal lines
        c.setFont("Helvetica", 10)
        for row in range(body_rows):
            y = table_top - table_header_height - row * body_row_height
            c.line(table_left, y, table_left + table_width, y)
        
        # Body data - vertically centered
        table_data = data.get("production_table", [])
        wrap_columns = {"bulk_bag_qty", "notes"}
        for row_idx in range(min(body_rows, len(table_data))):
            row_data = table_data[row_idx] or {}
            cell_top = table_top - table_header_height - row_idx * body_row_height
            cell_bottom = cell_top - body_row_height
            cell_center_y = cell_bottom + body_row_height / 2
            
            for col_idx, key in enumerate(["bulk_plastic_bag_lot_codes", "bulk_bag_qty", "pallet_num", "total_kg", "notes", "initial"]):
                value = row_data.get(key, "")
                if not value:
                    continue
                
                text_x = x_positions[col_idx] + 0.2 * cm
                
                if key in wrap_columns:
                    text_obj = c.beginText()
                    text_obj.setFont("Helvetica", 10)
                    text_obj.setLeading(11)
                    
                    max_width = column_specs[col_idx][1] * table_width - 0.4 * cm
                    words = str(value).split()
                    lines = []
                    current_line = ""
                    for word in words:
                        candidate = f"{current_line} {word}".strip()
                        if c.stringWidth(candidate, "Helvetica", 10) <= max_width:
                            current_line = candidate
                        else:
                            if current_line:
                                lines.append(current_line)
                            current_line = word
                    if current_line:
                        lines.append(current_line)
                    
                    # Center wrapped text vertically
                    total_text_height = len(lines) * 11
                    text_start_y = cell_center_y + total_text_height / 2 - 5
                    text_obj.setTextOrigin(text_x, text_start_y)
                    for line in lines:
                        text_obj.textLine(line)
                    c.drawText(text_obj)
                else:
                    # Center single line text vertically
                    c.drawString(text_x, cell_center_y - 0.2 * cm, str(value))
        
        # Production Notes와 Supervisor Name & Signature 행 (테이블 바로 아래)
        notes_signature_row_height = body_row_height  # 테이블 행과 같은 높이
        notes_signature_top = table_bottom
        notes_signature_bottom = notes_signature_top - notes_signature_row_height
        notes_signature_width = table_width / 2  # 반반으로 나누기
        
        # 테두리 그리기
        c.rect(table_left, notes_signature_bottom, table_width, notes_signature_row_height)
        # 중간 구분선
        c.line(table_left + notes_signature_width, notes_signature_bottom, 
               table_left + notes_signature_width, notes_signature_top)
        
        # Production Notes (왼쪽 반)
        notes_label_x = table_left + 0.2 * cm
        notes_label_y = notes_signature_bottom + notes_signature_row_height / 2
        c.setFont("Helvetica-Bold", 11)
        c.drawString(notes_label_x, notes_label_y - 0.2 * cm, "Production Notes:")
        
        notes_text = data.get("production_notes", "")
        if notes_text:
            c.setFont("Helvetica", 10)
            text_object = c.beginText()
            text_object.setTextOrigin(notes_label_x, notes_label_y - 0.5 * cm)
            text_object.setLeading(11)
            max_width = notes_signature_width - 0.4 * cm
            words = str(notes_text).split()
            lines = []
            current_line = ""
            for word in words:
                candidate = f"{current_line} {word}".strip()
                if c.stringWidth(candidate, "Helvetica", 10) <= max_width:
                    current_line = candidate
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            for line in lines[:3]:  # 최대 3줄
                text_object.textLine(line)
            c.drawText(text_object)
        
        # Supervisor Name & Signature (오른쪽 반)
        supervisor_label_x = table_left + notes_signature_width + 0.2 * cm
        supervisor_label_y = notes_signature_bottom + notes_signature_row_height / 2
        c.setFont("Helvetica-Bold", 11)
        c.drawString(supervisor_label_x, supervisor_label_y - 0.2 * cm, "Supervisor Name & Signature:")
        
        supervisor_text = data.get("supervisor_signature", "")
        if supervisor_text:
            c.setFont("Helvetica", 10)
            c.drawString(supervisor_label_x, supervisor_label_y - 0.5 * cm, supervisor_text)
        
        # Verification by QA와 Date 행 (Production Notes/Supervisor 아래)
        verification_row_height = body_row_height  # 테이블 행과 같은 높이
        verification_top = notes_signature_bottom - 0.1 * cm
        verification_bottom = verification_top - verification_row_height
        verification_width = table_width / 2  # 반반으로 나누기
        
        # Verification by QA (왼쪽 반)
        verification_center_y = verification_bottom + verification_row_height / 2 - 0.2 * cm
        verification_label_x = table_left + 0.2 * cm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(verification_label_x, verification_center_y - 0.2 * cm, "Verification by QA:")
        
        # 밑줄 (텍스트와 같은 높이)
        line_y = verification_center_y - 0.3 * cm
        line_start = verification_label_x + 3.8 * cm
        line_end = table_left + verification_width - 0.3 * cm
        c.line(line_start, line_y, line_end, line_y)
        
        verification_text = data.get("verified_by_qa", "")
        if verification_text:
            c.setFont("Helvetica", 10)
            c.drawString(line_start + 0.2 * cm, line_y - 0.1 * cm, verification_text)
        
        # Date (오른쪽 반)
        date_center_y = verification_bottom + verification_row_height / 2 -0.2 * cm
        date_label_x = table_left + verification_width + 0.2 * cm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(date_label_x, date_center_y - 0.2 * cm, "Date:")
        
        # 밑줄 (Date 텍스트 아래)
        date_line_y = date_center_y - 0.3 * cm
        date_line_start = date_label_x + 1.0 * cm
        date_line_end = table_left + table_width - 0.3 * cm
        c.line(date_line_start, date_line_y, date_line_end, date_line_y)
        
        date_text = data.get("sign_date", "")
        if date_text:
            c.setFont("Helvetica", 10)
            c.drawString(date_line_start + 0.2 * cm, date_line_y + 0.2 * cm, date_text)
        
        c.setFont("Helvetica", 9)
        c.drawRightString(page_width - margin, margin - 0.4 * cm, "Page 1")
        c.drawString(margin, margin - 0.4 * cm, "Inno Foods Inc.")
        
        c.save()
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
    
    def print_label(self, pdf_path, printer_name=None, label_data=None, copies=1):
        """라벨 인쇄"""
        try:
            try:
                copies = int(copies)
            except (ValueError, TypeError):
                copies = 1
            if copies < 1:
                copies = 1
            
            # CUPS를 통한 인쇄 (Linux/macOS)
            if os.name == 'posix':
                cmd = ['lp']
                if printer_name:
                    cmd.extend(['-d', printer_name])
                if copies > 1:
                    cmd.extend(['-n', str(copies)])
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
                    success = True
                    for i in range(copies):
                        if not self.print_simple_pdf(pdf_path, printer_name):
                            success = False
                            break
                    return success
                else:
                    # 기본 프린터로 인쇄
                    for i in range(copies):
                        os.startfile(pdf_path, "print")
                    logger.info(f"라벨이 기본 프린터로 인쇄되었습니다: {pdf_path} (copies={copies})")
                    return True
        except Exception as e:
            logger.error(f"인쇄 중 오류 발생: {str(e)}")
            return False
    
    def print_simple_pdf(self, pdf_path, printer_name, copies=1):
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
                    for i in range(copies):
                        for copy_idx in range(max(1, copies)):
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
                
                success = True
                for copy_idx in range(max(1, copies)):
                    result = subprocess.run([
                        'powershell', '-Command', ps_script
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        print(f"✅ Adobe Reader를 통해 프린터 '{printer_name}'로 PDF 인쇄 성공 (copy {copy_idx + 1}/{copies})")
                        logger.info(f"프린터 '{printer_name}'로 PDF 인쇄 성공 (copy {copy_idx + 1}/{copies})")
                        if copies > 1 and copy_idx < copies - 1:
                            import time  # pylint: disable=import-outside-toplevel
                            time.sleep(1)
                    else:
                        print(f"⚠️ Adobe Reader 방법 실패: {result.stderr}")
                        print("대체 방법: 기본 프린터 임시 변경 후 인쇄...")
                        success = False
                        break
                
                if success:
                    return True
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
                        for copy_idx in range(max(1, copies)):
                            os.startfile(pdf_path, 'print')
                            print(f"✅ PDF가 프린터로 전송되었습니다: {current_printer} (copy {copy_idx + 1}/{copies})")
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
                        for copy_idx in range(max(1, copies)):
                            os.startfile(pdf_path, 'print')
                        return True
                        
                except Exception as e2:
                    print(f"❌ 기본 프린터 변경 방법도 실패: {e2}")
                    print("기본 프린터로 인쇄합니다.")
                    for copy_idx in range(max(1, copies)):
                        os.startfile(pdf_path, 'print')
                    return True
            
        except ImportError:
            print("❌ win32print 모듈이 없습니다. pip install pywin32로 설치해주세요.")
            # win32print가 없으면 기본 방법으로 인쇄
            for copy_idx in range(max(1, copies)):
                os.startfile(pdf_path, "print")
            logger.info(f"PDF가 기본 프린터로 인쇄됨: {pdf_path}")
            return True
            
        except Exception as e:
            logger.error(f"PDF 인쇄 실패: {e}")
            print(f"❌ 인쇄 중 오류 발생: {e}")
            
            # 오류 발생 시 기본 방법으로 인쇄
            try:
                print("기본 방법으로 인쇄 시도...")
                for copy_idx in range(max(1, copies)):
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
        self.root.geometry("1400x900")
        self.root.resizable(True, True)
        # 윈도우 최대화
        if os.name == 'nt':  # Windows
            self.root.state('zoomed')
        else:  # Linux/macOS
            self.root.attributes('-zoomed', True)
        
        # 프린터 인스턴스
        self.printer = LabelPrinter()
        
        # Flask 서버 관련
        self.flask_app = None
        self.server_thread = None
        self.server_running = False
        
        # 인쇄 기록 저장
        self.print_history = []
        
        # 양식 데이터 저장
        self.production_records = []
        self.load_production_records()
        
        # 라벨 크기 설정 (TXT 파일에서 읽기)
        self.label_width_cm = 10.0  # 기본값
        self.label_height_cm = 5.0  # 기본값
        self.font_name = "Arial"  # 기본값
        self.font_size = 48  # 기본값
        self.extra_weight = 3.0  # 기본 기타 무게
        self.default_printer_name = None
        self.default_label_copies = 2
        self.default_bulk_copies = 2
        self._font_loaded_from_settings = False
        self.load_label_size_from_txt()
        
        # 폰트 설정 (TXT 파일에서 읽기)
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
                    for raw_line in f:
                        line = raw_line.strip()
                        if not line or line.startswith('#'):
                            continue
                        
                        key = None
                        value = None
                        
                        if ',' in line:
                            parts = [p.strip() for p in line.split(',')]
                            if len(parts) == 2:
                                try:
                                    self.label_width_cm = float(parts[0])
                                    self.label_height_cm = float(parts[1])
                                except ValueError:
                                    pass
                                continue
                        
                        if ':' in line:
                            key, value = [token.strip() for token in line.split(':', 1)]
                            key_lower = key.lower()
                            
                            if key_lower in ('width', '너비'):
                                try:
                                    self.label_width_cm = float(value)
                                except ValueError:
                                    pass
                            elif key_lower in ('height', '높이'):
                                try:
                                    self.label_height_cm = float(value)
                                except ValueError:
                                    pass
                            elif key_lower == 'font':
                                self.font_name = value
                                self._font_loaded_from_settings = True
                            elif key_lower in ('fontsize', 'font_size', '폰트크기'):
                                try:
                                    self.font_size = int(float(value))
                                    self._font_loaded_from_settings = True
                                except ValueError:
                                    pass
                            elif key_lower in ('extra_weight', 'extraweight', 'tare', '기타무게'):
                                try:
                                    self.extra_weight = float(value)
                                except ValueError:
                                    pass
                            elif key_lower in ('default_printer', 'defaultprinter'):
                                if value:
                                    self.default_printer_name = value
                            elif key_lower in ('default_label_copies', 'label_copies', '라벨매수'):
                                try:
                                    self.default_label_copies = int(float(value))
                                except ValueError:
                                    pass
                            elif key_lower in ('default_bulk_copies', 'bulk_copies', '벌크매수'):
                                try:
                                    self.default_bulk_copies = int(float(value))
                                except ValueError:
                                    pass
                print(f"라벨 크기 설정 로드: {self.label_width_cm}cm x {self.label_height_cm}cm")
        except Exception as e:
            print(f"라벨 크기 설정 파일 읽기 실패: {e}, 기본값 사용")
    
    def load_font_from_txt(self):
        """TXT 파일에서 폰트 설정 읽기"""
        if getattr(self, '_font_loaded_from_settings', False):
            return
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
    
    def save_settings(self):
        """현재 설정을 label_size.txt에 저장"""
        try:
            config_file = "label_size.txt"
            lines = [
                f"{self.label_width_cm:g},{self.label_height_cm:g}",
                f"font: {self.font_name}",
                f"fontsize: {self.font_size}",
                f"extra_weight: {self.extra_weight:g}",
                f"default_label_copies: {self.default_label_copies}",
                f"default_bulk_copies: {self.default_bulk_copies}",
            ]
            if self.default_printer_name:
                lines.append(f"default_printer: {self.default_printer_name}")
            
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(str(line) for line in lines))
                f.write('\n')
        except Exception as e:
            print(f"설정 저장 실패: {e}")
    
    def on_font_changed(self, *args):
        """폰트 변경 시 미리보기 업데이트"""
        try:
            self.font_name = self.font_name_var.get() or "Arial"
            self.font_size = int(float(self.font_size_var.get() or "48"))
            if hasattr(self, 'label_canvas'):
                self.update_label_preview()
            self.save_settings()
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
        # 메인 프레임 (전체 레이아웃)
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 왼쪽 프레임 (라벨 입력 폼)
        left_frame = ttk.Frame(main_container, padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 오른쪽 프레임 (양식 입력 폼)
        right_frame = ttk.LabelFrame(main_container, text="Daily Bulk Production Sheet", padding="5")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 제목 (왼쪽)
        title_label = ttk.Label(left_frame, text="라벨 인쇄 프로그램", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 서버 상태
        self.setup_server_status(left_frame)
        
        # 라벨 입력 폼
        self.setup_label_form(left_frame)
        
        # 버튼들
        self.setup_buttons(left_frame)
        
        # 프린터 정보
        self.setup_printer_info(left_frame)
        
        # 오른쪽에 양식 입력 폼 추가
        self.setup_production_form_inline(right_frame)
        
        # 그리드 가중치 설정 (왼쪽:오른쪽 = 1:3로 조정)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(0, weight=1)  # 왼쪽 프레임
        main_container.columnconfigure(1, weight=3)  # 오른쪽 프레임을 더 크게
        main_container.rowconfigure(0, weight=1)
        left_frame.columnconfigure(1, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        
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
        self.total_weight_entry = ttk.Entry(form_frame, textvariable=self.total_weight_var, width=15)
        self.total_weight_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))
        self.total_weight_var.trace_add('write', self.calculate_net_weight)
        
        # 팔렛무게
        ttk.Label(form_frame, text="팔렛무게 (kg):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.pallet_weight_var = tk.StringVar()
        self.pallet_weight_entry = ttk.Entry(form_frame, textvariable=self.pallet_weight_var, width=15)
        self.pallet_weight_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))
        self.pallet_weight_var.trace_add('write', self.calculate_net_weight)
        
        # 기타 무게
        ttk.Label(form_frame, text="기타 무게 (kg):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.extra_weight_var = tk.StringVar(value=str(self.extra_weight))
        ttk.Entry(form_frame, textvariable=self.extra_weight_var, width=15).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))
        self.extra_weight_var.trace_add('write', self.on_extra_weight_changed)
        
        # 순수무게 (자동 계산)
        ttk.Label(form_frame, text="순수무게 (kg):").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.net_weight_var = tk.StringVar()
        self.net_weight_label = ttk.Label(form_frame, textvariable=self.net_weight_var, foreground="blue", font=("Arial", 10, "bold"))
        self.net_weight_label.grid(row=3, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        # 날짜 (자동 설정)
        ttk.Label(form_frame, text="날짜:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        self.date_label = ttk.Label(form_frame, textvariable=self.date_var, foreground="gray")
        self.date_label.grid(row=4, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        # 폰트 설정
        font_frame = ttk.Frame(form_frame)
        font_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        
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
        ttk.Label(form_frame, text="프린터 선택:").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.printer_var = tk.StringVar()
        self.printer_combo = ttk.Combobox(form_frame, textvariable=self.printer_var, state="readonly", width=15)
        self.printer_combo.grid(row=6, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))
        self.printer_combo.bind("<<ComboboxSelected>>", self.on_printer_selected)
        
        # 인쇄 매수
        ttk.Label(form_frame, text="인쇄 매수:").grid(row=7, column=0, sticky=tk.W, pady=2)
        self.copies_var = tk.StringVar(value=str(self.default_label_copies))
        ttk.Entry(form_frame, textvariable=self.copies_var, width=10).grid(row=7, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        # 라벨 미리보기 영역 추가
        self.setup_label_preview(form_frame)
        self.calculate_net_weight()
    
    def setup_label_preview(self, parent):
        """라벨 미리보기 Canvas 설정"""
        preview_frame = ttk.LabelFrame(parent, text="라벨 미리보기", padding="5")
        preview_frame.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Canvas 생성 (라벨 용지 사이즈에 맞게, 1.5배 크기로 미리보기 - 더 작게)
        # 1cm = 37.8 pixels @ 96 DPI
        # 1.5배 미리보기: 1cm = 56.7 pixels
        # 라벨 용지 사이즈 기준으로 캔버스 크기 설정
        canvas_width = int(self.label_width_cm * 1.5 * 37.8)
        canvas_height = int(self.label_height_cm * 1.5 * 37.8)
        
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
        # 라벨 용지 사이즈 기준 계산: 1.5배 미리보기
        base_canvas_width = int(self.label_width_cm * 1.5 * 37.8)  # 1cm = 56.7 pixels (1.5배)
        base_canvas_height = int(self.label_height_cm * 1.5 * 37.8)
        
        width = canvas.winfo_width() if canvas.winfo_width() > 1 else base_canvas_width
        height = canvas.winfo_height() if canvas.winfo_height() > 1 else base_canvas_height
        
        # 실제 인쇄 크기 (300 DPI 기준)와 미리보기 캔버스 크기 (96 DPI 기준)의 비율 계산
        # 실제 인쇄: label_width_cm * 118.11 pixels (300 DPI에서 1cm = 118.11 pixels)
        # 미리보기: label_width_cm * 1.5 * 37.8 pixels (96 DPI에서 1cm = 37.8 pixels, 1.5배)
        # 미리보기 / 실제 인쇄 = (1.5 * 37.8) / 118.11 ≈ 0.48
        # 따라서 폰트 크기도 이 비율로 조정해야 함
        
        # 실제 인쇄 시 사용할 크기 (300 DPI 기준)
        actual_print_width = self.label_width_cm * 118.11
        actual_print_height = self.label_height_cm * 118.11
        
        # 미리보기 캔버스 크기와 실제 인쇄 크기의 비율
        width_ratio = width / actual_print_width
        height_ratio = height / actual_print_height
        # 폰트 크기는 작은 비율을 사용 (어느 쪽이든 넘치지 않도록)
        scale = min(width_ratio, height_ratio)
        
        # Canvas 크기에 비례하여 폰트 크기 조정
        base_font_size = self.font_size  # 설정된 폰트 크기 사용
        
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
            extra_weight = self.extra_weight_var.get() or "0"
            try:
                total_val = float(total_weight)
            except ValueError:
                total_val = 0
            try:
                pallet_val = float(pallet_weight)
            except ValueError:
                pallet_val = 0
            try:
                extra_val = float(extra_weight)
            except ValueError:
                extra_val = 0
            net_weight = total_val - pallet_val - extra_val
            
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
        ttk.Button(button_frame, text="양식 기록", command=self.open_production_form).pack(side=tk.LEFT, padx=5)
        
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
    
    def setup_production_form_inline(self, parent):
        """Daily Bulk Production Sheet 양식을 오른쪽에 인라인으로 표시"""
        # 저장 버튼 (상단에 먼저 배치)
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=5, fill=tk.X)
        
        def auto_save_form():
            """양식 데이터 자동 저장 (production_table 포함)"""
            date_value = self.form_data_inline['date'].get()
            shift_value = self.form_data_inline['shift'].get()
            
            if not date_value or not shift_value:
                return  # date나 shift가 없으면 저장하지 않음
            
            record = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'date': date_value,
                'shift': shift_value,
                'supervisor_name': self.form_data_inline['supervisor_name'].get(),
                'employee_name': self.form_data_inline['employee_name'].get(),
                'product_name': self.form_data_inline['product_name'].get(),
                'bulk_lot_code': self.form_data_inline['bulk_lot_code'].get(),
                'parchment_reuse': self.form_data_inline['parchment_reuse'].get(),
                'parchment_lot_code': self.form_data_inline['parchment_lot_code'].get(),
                'no_choco_coating': self.form_data_inline['no_choco_coating'].get(),
                'quantity': self.form_data_inline['quantity'].get(),
                'quality_checked': self.form_data_inline['quality_checked'].get(),
                'production_table': [
                    {
                        'bulk_plastic_bag_lot_codes': row['bulk_plastic_bag_lot_codes'].get(),
                        'bulk_bag_qty': row['bulk_bag_qty'].get(),
                        'pallet_num': row['pallet_num'].get(),
                        'total_kg': row['total_kg'].get(),
                        'notes': row['notes'].get(),
                        'initial': row['initial'].get()
                    }
                    for row in self.table_data_inline
                ],
                'production_notes': "",
                'verified_by_qa': "",
                'supervisor_signature': ""
            }
            
            # date + shift로 중복 체크
            existing_idx = None
            for idx, existing_record in enumerate(self.production_records):
                if existing_record.get('date') == date_value and existing_record.get('shift') == shift_value:
                    existing_idx = idx
                    break
            
            if existing_idx is not None:
                # 중복이면 덮어쓰기
                self.production_records[existing_idx] = record
            else:
                # 새로 추가
                self.production_records.append(record)
            
            self.save_production_records()
        
        def save_inline_form():
            """양식 데이터 저장 (수동 저장)"""
            auto_save_form()
            date_value = self.form_data_inline['date'].get()
            shift_value = self.form_data_inline['shift'].get()
            messagebox.showinfo("성공", f"양식이 저장되었습니다. (Date: {date_value}, Shift: {shift_value})")
        
        def fill_from_label_inline():
            """현재 라벨 데이터를 양식의 TOTAL KG에 자동 입력 (순수무게)"""
            label_data = self.get_label_data()
            net_weight = label_data.get('net_weight', '')
            
            if net_weight:
                # 첫 번째 빈 행에 Total KG 입력 (순수무게)
                for row_data in self.table_data_inline:
                    if not row_data['total_kg'].get():
                        row_data['total_kg'].set(net_weight)
                        break
        
        self.bulk_copies_var = tk.StringVar(value=str(self.default_bulk_copies))
        ttk.Label(button_frame, text="인쇄 매수:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(button_frame, textvariable=self.bulk_copies_var, width=6).pack(side=tk.LEFT, padx=(0, 10))
        
        def clear_production_table():
            """Production Data Table의 모든 데이터 초기화"""
            if messagebox.askyesno("확인", "Production Data Table의 모든 데이터를 초기화하시겠습니까?"):
                for row_data in self.table_data_inline:
                    for key, var in row_data.items():
                        var.set("")
                messagebox.showinfo("완료", "Production Data Table이 초기화되었습니다.")
        
        ttk.Button(button_frame, text="라벨 데이터 가져오기", command=fill_from_label_inline).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="미리보기", command=self.preview_bulk_sheet_inline).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="인쇄", command=self.print_bulk_sheet_inline).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="저장", command=save_inline_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="저장된 양식 불러오기", command=self.load_saved_bulk_sheet).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="테이블 초기화", command=clear_production_table).pack(side=tk.LEFT, padx=5)
        
        # 스크롤 가능한 프레임
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # canvas window ID 저장
        self.canvas_window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        def update_scroll_region(event):
            """scrollable_frame 크기 변경 시 스크롤 영역 업데이트"""
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def update_canvas_width(event):
            """canvas 너비 변경 시 scrollable_frame 너비 조정"""
            canvas_width = event.width
            canvas.itemconfig(self.canvas_window_id, width=canvas_width)
        
        scrollable_frame.bind("<Configure>", update_scroll_region)
        canvas.bind('<Configure>', update_canvas_width)
        
        # 양식 입력 필드들
        self.form_data_inline = {}
        
        # 제목
        title_label = ttk.Label(scrollable_frame, text="Daily Bulk Production Sheet", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=5)
        
        # DATE
        ttk.Label(scrollable_frame, text="DATE:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        date_entry = ttk.Entry(scrollable_frame, textvariable=date_var, width=20)
        date_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        self.form_data_inline['date'] = date_var
        # 자동 저장 (공유 타이머 사용)
        def trigger_auto_save(*args):
            if hasattr(self, '_auto_save_timer'):
                self.root.after_cancel(self._auto_save_timer)
            self._auto_save_timer = self.root.after(2000, auto_save_form)
        
        date_var.trace_add('write', trigger_auto_save)
        
        # SHIFT
        ttk.Label(scrollable_frame, text="SHIFT:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        shift_var = tk.StringVar(value="AM")
        shift_frame = ttk.Frame(scrollable_frame)
        shift_frame.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        ttk.Radiobutton(shift_frame, text="AM", variable=shift_var, value="AM").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(shift_frame, text="PM", variable=shift_var, value="PM").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(shift_frame, text="Graveyard", variable=shift_var, value="Graveyard").pack(side=tk.LEFT, padx=2)
        self.form_data_inline['shift'] = shift_var
        # 자동 저장
        shift_var.trace_add('write', trigger_auto_save)
        
        # Supervisor Name
        ttk.Label(scrollable_frame, text="Supervisor Name:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        supervisor_var = tk.StringVar()
        supervisor_entry = ttk.Entry(scrollable_frame, textvariable=supervisor_var, width=20)
        supervisor_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        self.form_data_inline['supervisor_name'] = supervisor_var
        
        # Employee Name
        ttk.Label(scrollable_frame, text="Employee Name:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=2)
        employee_var = tk.StringVar()
        employee_entry = ttk.Entry(scrollable_frame, textvariable=employee_var, width=20)
        employee_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        self.form_data_inline['employee_name'] = employee_var
        
        # Product Name
        ttk.Label(scrollable_frame, text="Product Name:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=2)
        product_var = tk.StringVar()
        product_entry = ttk.Entry(scrollable_frame, textvariable=product_var, width=20)
        product_entry.grid(row=5, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        self.form_data_inline['product_name'] = product_var
        
        # Bulk Lot Code
        ttk.Label(scrollable_frame, text="Bulk Lot Code:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=2)
        bulk_lot_var = tk.StringVar()
        bulk_lot_entry = ttk.Entry(scrollable_frame, textvariable=bulk_lot_var, width=20)
        bulk_lot_entry.grid(row=6, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        self.form_data_inline['bulk_lot_code'] = bulk_lot_var
        
        # Parchment Paper
        ttk.Label(scrollable_frame, text="Parchment Paper:").grid(row=7, column=0, sticky=tk.W, padx=5, pady=2)
        parchment_frame = ttk.Frame(scrollable_frame)
        parchment_frame.grid(row=7, column=1, sticky=tk.W, padx=5, pady=2)
        parchment_reuse_var = tk.BooleanVar()
        ttk.Checkbutton(parchment_frame, text="Reuse", variable=parchment_reuse_var).pack(side=tk.LEFT, padx=2)
        ttk.Label(parchment_frame, text="or Lot:").pack(side=tk.LEFT, padx=2)
        parchment_lot_var = tk.StringVar()
        parchment_lot_entry = ttk.Entry(parchment_frame, textvariable=parchment_lot_var, width=12)
        parchment_lot_entry.pack(side=tk.LEFT, padx=2)
        self.form_data_inline['parchment_reuse'] = parchment_reuse_var
        self.form_data_inline['parchment_lot_code'] = parchment_lot_var
        
        # No need for choco coating 체크박스
        no_choco_var = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text="No need for choco coating", variable=no_choco_var).grid(row=8, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
        self.form_data_inline['no_choco_coating'] = no_choco_var
        
        # Quantity
        ttk.Label(scrollable_frame, text="Quantity:").grid(row=9, column=0, sticky=tk.W, padx=5, pady=2)
        quantity_var = tk.StringVar()
        quantity_entry = ttk.Entry(scrollable_frame, textvariable=quantity_var, width=20)
        quantity_entry.grid(row=9, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        self.form_data_inline['quantity'] = quantity_var
        
        # Quality Checked
        ttk.Label(scrollable_frame, text="Quality Checked (Initial):").grid(row=10, column=0, sticky=tk.W, padx=5, pady=2)
        quality_var = tk.StringVar()
        quality_entry = ttk.Entry(scrollable_frame, textvariable=quality_var, width=20)
        quality_entry.grid(row=10, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        self.form_data_inline['quality_checked'] = quality_var
        
        # Production Data Table
        table_label = ttk.Label(scrollable_frame, text="Production Data Table", font=("Arial", 11, "bold"))
        table_label.grid(row=11, column=0, columnspan=2, pady=(10, 5))
        
        # 테이블 헤더 (PDF와 동일하게)
        headers = ["Bulk Plastic Bag\nLot Codes", "Bulk Bag\nQTY", "Pallet #", "Total KG", "Notes", "Initial"]
        # PDF의 컬럼 비율 (column_specs와 동일) - 정수로 변환 (100배)
        column_weights = [28, 14, 13, 13, 24, 8]
        header_frame = ttk.Frame(scrollable_frame)
        header_frame.grid(row=12, column=0, columnspan=6, sticky=(tk.W, tk.E), padx=5, pady=2)
        # 헤더 프레임의 컬럼 가중치 설정 (PDF 비율과 동일하게)
        for col in range(6):
            header_frame.columnconfigure(col, weight=column_weights[col])
        for col, header in enumerate(headers):
            # 컬럼별로 다른 padx 설정: 첫 번째는 더 넓게, 마지막은 더 좁게
            if col == 0:  # 첫 번째 컬럼 (Lot Codes)
                header_padx = 5
            elif col == 5:  # 마지막 컬럼 (Initial)
                header_padx = 1
            else:
                header_padx = 3
            # 줄바꿈 처리
            if '\n' in header:
                lines = header.split('\n')
                header_label = tk.Label(header_frame, text='\n'.join(lines), font=("Arial", 9, "bold"), 
                         relief=tk.SOLID, borderwidth=1, padx=header_padx, pady=5, justify=tk.CENTER)
            else:
                header_label = tk.Label(header_frame, text=header, font=("Arial", 9, "bold"), 
                         relief=tk.SOLID, borderwidth=1, padx=header_padx, pady=5)
            header_label.grid(row=0, column=col, sticky=(tk.W, tk.E, tk.N, tk.S), padx=1, ipadx=0)
        
        # 테이블 행 (15개 행) - 헤더와 같은 프레임 구조 사용
        self.table_data_inline = []
        header_keys = ['bulk_plastic_bag_lot_codes', 'bulk_bag_qty', 'pallet_num', 'total_kg', 'notes', 'initial']
        for row in range(15):
            row_frame = ttk.Frame(scrollable_frame)
            row_frame.grid(row=13+row, column=0, columnspan=6, sticky=(tk.W, tk.E), padx=5, pady=1)
            # 행 프레임의 컬럼 가중치 설정 (PDF 비율과 동일하게)
            for col in range(6):
                row_frame.columnconfigure(col, weight=column_weights[col])
            row_data = {}
            for col, key in enumerate(header_keys):
                var = tk.StringVar()
                # 컬럼별로 다른 width 설정 (문자 단위) - 직접 조절 가능
                if col == 0:  # 첫 번째 컬럼 (Lot Codes) - 더 넓게
                    entry_width = 25
                elif col == 1:  # Bulk Bag QTY
                    entry_width = 13
                elif col == 2:  # Pallet #
                    entry_width = 12
                elif col == 3:  # Total KG
                    entry_width = 12
                elif col == 4:  # Notes
                    entry_width = 13
                else:  # Initial (col == 5) - 더 좁게
                    entry_width = 8
                entry = tk.Entry(row_frame, textvariable=var, relief=tk.SOLID, borderwidth=1, 
                               font=("Arial", 9), width=entry_width)
                entry.grid(row=0, column=col, sticky=(tk.W, tk.E, tk.N, tk.S), padx=1)
                row_data[key] = var
                
                # 첫 번째 행의 Lot code와 Bag QTY 변경 시 다음 행들에 복사 (비어있을 때만)
                if row == 0 and (key == 'bulk_plastic_bag_lot_codes' or key == 'bulk_bag_qty'):
                    var.trace_add('write', lambda name, index, mode, var=var, key=key, row_idx=row: self.copy_to_next_rows(key, var, row_idx))
                
                # Total KG 입력 시 Pallet 번호 자동 증가 및 자동 저장
                if key == 'total_kg':
                    def on_total_kg_change(name, index, mode, var=var, row_idx=row):
                        self.auto_increment_pallet(row_idx)
                        # 자동 저장 (약간의 지연을 두어 연속 입력 시 과도한 저장 방지)
                        trigger_auto_save()
                    var.trace_add('write', on_total_kg_change)
                
                # 다른 필드 변경 시에도 자동 저장 (Total KG 제외)
                if key != 'total_kg':
                    var.trace_add('write', trigger_auto_save)
            
            self.table_data_inline.append(row_data)
        self.form_data_inline['production_table'] = self.table_data_inline
        
        # 그리드 가중치 설정
        scrollable_frame.columnconfigure(1, weight=1)
        for col in range(6):
            scrollable_frame.columnconfigure(col, weight=1)
        
        # 스크롤바와 캔버스 배치
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def collect_bulk_sheet_data_inline(self):
        """오른쪽 인라인 양식에서 벌크 생산 시트 데이터를 수집"""
        if not hasattr(self, 'form_data_inline'):
            messagebox.showerror("오류", "벌크 생산 시트 양식이 초기화되지 않았습니다.")
            return None
        
        data = {
            'date': self.form_data_inline['date'].get(),
            'shift': self.form_data_inline['shift'].get(),
            'supervisor_name': self.form_data_inline['supervisor_name'].get(),
            'employee_name': self.form_data_inline['employee_name'].get(),
            'product_name': self.form_data_inline['product_name'].get(),
            'bulk_lot_code': self.form_data_inline['bulk_lot_code'].get(),
            'quantity': self.form_data_inline['quantity'].get(),
            'parchment_reuse': bool(self.form_data_inline['parchment_reuse'].get()),
            'parchment_lot_code': self.form_data_inline['parchment_lot_code'].get(),
            'no_choco_coating': bool(self.form_data_inline['no_choco_coating'].get()),
            'quality_checked': self.form_data_inline['quality_checked'].get(),
            'verified_by_qa': "",
            'supervisor_signature': "",
            'sign_date': self.form_data_inline['date'].get(),
            'copies': self.bulk_copies_var.get() if hasattr(self, 'bulk_copies_var') else str(self.default_bulk_copies),
            'production_notes': ""
        }
        
        table_entries = []
        for row_vars in self.table_data_inline:
            row_data = {}
            empty = True
            for key, var in row_vars.items():
                value = var.get()
                if value:
                    empty = False
                row_data[key] = value
            if not empty:
                table_entries.append(row_data)
        data['production_table'] = table_entries
        return data
    
    def preview_bulk_sheet_inline(self):
        """벌크 생산 시트 양식을 PDF로 미리보기"""
        data = self.collect_bulk_sheet_data_inline()
        if data is None:
            return
        
        try:
            pdf_path = self.printer.create_bulk_production_sheet_pdf(data)
            if os.name == 'nt':
                os.startfile(pdf_path)
            else:
                webbrowser.open_new(pdf_path)
        except Exception as e:
            messagebox.showerror("오류", f"미리보기 생성 중 오류가 발생했습니다: {e}")
    
    def print_bulk_sheet_inline(self):
        """벌크 생산 시트를 기본 프린터로 인쇄"""
        data = self.collect_bulk_sheet_data_inline()
        if data is None:
            return
        
        try:
            copies_value = data.get('copies', self.default_bulk_copies)
            try:
                copies = int(copies_value)
            except (ValueError, TypeError):
                copies = self.default_bulk_copies
            if copies < 1:
                messagebox.showerror("오류", "인쇄 매수는 1 이상의 정수여야 합니다.")
                return
            data['copies'] = str(copies)
            pdf_path = self.printer.create_bulk_production_sheet_pdf(data)
            success = self.printer.print_label(pdf_path, copies=copies)
            if success:
                messagebox.showinfo("성공", "벌크 생산 시트가 기본 프린터로 인쇄되었습니다.")
            else:
                messagebox.showerror("오류", "인쇄에 실패했습니다. 프린터 설정을 확인해주세요.")
        except Exception as e:
            messagebox.showerror("오류", f"인쇄 중 오류가 발생했습니다: {e}")
    
    def copy_to_next_rows(self, key, first_row_var, first_row_idx):
        """첫 번째 행의 Lot code나 Bag QTY를 다음 행들에 복사 (Total KG이 입력된 행에만)"""
        if not hasattr(self, 'table_data_inline'):
            return
        
        value = first_row_var.get()
        if not value:
            return
        
        # 첫 번째 행을 제외한 나머지 행에 복사
        # 단, Total KG이 입력된 행에만 복사
        for i in range(1, len(self.table_data_inline)):
            if key in self.table_data_inline[i]:
                # Total KG이 입력된 행에만 복사
                total_kg_value = self.table_data_inline[i]['total_kg'].get()
                if total_kg_value:  # Total KG이 있으면
                    # 현재 값이 비어있을 때만 복사
                    current_value = self.table_data_inline[i][key].get()
                    if not current_value:
                        self.table_data_inline[i][key].set(value)
    
    def auto_increment_pallet(self, row_idx):
        """Total KG 입력 시 Pallet 번호 자동 증가"""
        if not hasattr(self, 'table_data_inline'):
            return
        
        total_kg_value = self.table_data_inline[row_idx]['total_kg'].get()
        
        # Total KG이 입력되고 Pallet 번호가 비어있을 때만 자동 증가
        if total_kg_value and not self.table_data_inline[row_idx]['pallet_num'].get():
            # 이전 행들의 Pallet 번호를 확인하여 다음 번호 결정
            max_pallet = 0
            for i in range(row_idx):
                pallet_str = self.table_data_inline[i]['pallet_num'].get()
                if pallet_str:
                    try:
                        pallet_num = int(pallet_str)
                        if pallet_num > max_pallet:
                            max_pallet = pallet_num
                    except ValueError:
                        pass
            
            # 다음 Pallet 번호 설정
            next_pallet = max_pallet + 1
            self.table_data_inline[row_idx]['pallet_num'].set(f"{next_pallet:03d}")
            
            # Lot code와 Bag QTY가 비어있으면 첫 번째 행의 값 복사
            lot_code = self.table_data_inline[row_idx]['bulk_plastic_bag_lot_codes'].get()
            bag_qty = self.table_data_inline[row_idx]['bulk_bag_qty'].get()
            
            if not lot_code and len(self.table_data_inline) > 0:
                first_lot = self.table_data_inline[0]['bulk_plastic_bag_lot_codes'].get()
                if first_lot:
                    self.table_data_inline[row_idx]['bulk_plastic_bag_lot_codes'].set(first_lot)
            
            if not bag_qty and len(self.table_data_inline) > 0:
                first_bag_qty = self.table_data_inline[0]['bulk_bag_qty'].get()
                if first_bag_qty:
                    self.table_data_inline[row_idx]['bulk_bag_qty'].set(first_bag_qty)
    
    def add_to_production_form(self, label_data):
        """모바일 API로 인쇄 시 양식 테이블에 Total KG 자동 추가 (순수무게)"""
        if not hasattr(self, 'table_data_inline'):
            return
        
        net_weight = label_data.get('net_weight', '')
        if not net_weight:
            return
        
        # 첫 번째 빈 행에 Total KG 입력 (순수무게)
        for i, row_data in enumerate(self.table_data_inline):
            current_total_kg = row_data['total_kg'].get()
            if not current_total_kg:
                # Total KG 입력 (순수무게)
                row_data['total_kg'].set(net_weight)
                
                # Pallet 번호 자동 증가
                if not row_data['pallet_num'].get():
                    max_pallet = 0
                    for j in range(i):
                        pallet_str = self.table_data_inline[j]['pallet_num'].get()
                        if pallet_str:
                            try:
                                pallet_num = int(pallet_str)
                                if pallet_num > max_pallet:
                                    max_pallet = pallet_num
                            except ValueError:
                                pass
                    
                    next_pallet = max_pallet + 1
                    row_data['pallet_num'].set(f"{next_pallet:03d}")
                
                # Lot code와 Bag QTY가 비어있으면 첫 번째 행의 값 복사
                if not row_data['bulk_plastic_bag_lot_codes'].get() and len(self.table_data_inline) > 0:
                    first_lot = self.table_data_inline[0]['bulk_plastic_bag_lot_codes'].get()
                    if first_lot:
                        row_data['bulk_plastic_bag_lot_codes'].set(first_lot)
                
                if not row_data['bulk_bag_qty'].get() and len(self.table_data_inline) > 0:
                    first_bag_qty = self.table_data_inline[0]['bulk_bag_qty'].get()
                    if first_bag_qty:
                        row_data['bulk_bag_qty'].set(first_bag_qty)
                
                break  # 첫 번째 빈 행에만 입력
    
    def on_extra_weight_changed(self, *args):
        """기타 무게 변경 시 처리"""
        value = self.extra_weight_var.get()
        try:
            self.extra_weight = float(value or 0)
            self.save_settings()
        except ValueError:
            # 숫자가 입력되지 않은 경우 저장하지 않음
            pass
        self.calculate_net_weight()
    
    def calculate_net_weight(self, *args):
        """순수무게 자동 계산"""
        try:
            total_weight = float(self.total_weight_var.get() or 0)
        except ValueError:
            total_weight = 0
        try:
            pallet_weight = float(self.pallet_weight_var.get() or 0)
        except ValueError:
            pallet_weight = 0
        try:
            extra_weight = float(self.extra_weight_var.get() or 0)
        except ValueError:
            extra_weight = self.extra_weight if isinstance(self.extra_weight, (int, float)) else 0
        
        net_weight = total_weight - pallet_weight - extra_weight
        if net_weight > 0:
            self.net_weight_var.set(f"{net_weight:.1f} kg")
        else:
            self.net_weight_var.set("0.0 kg")
    
    def reset_form(self):
        """폼 초기화"""
        self.total_weight_var.set("")
        self.pallet_weight_var.set("")
        self.net_weight_var.set("0.0 kg")
        self.date_var.set(datetime.now().strftime('%Y-%m-%d'))
        if hasattr(self, 'extra_weight_var'):
            self.extra_weight_var.set(str(self.extra_weight))
        if hasattr(self, 'copies_var'):
            self.copies_var.set(str(self.default_label_copies))
        self.calculate_net_weight()
        
    def get_label_data(self):
        """입력된 라벨 데이터 가져오기"""
        try:
            total_weight = float(self.total_weight_var.get() or 0)
            pallet_weight = float(self.pallet_weight_var.get() or 0)
            extra_weight = float(self.extra_weight_var.get() or 0)
            net_weight = total_weight - pallet_weight - extra_weight
        except ValueError:
            net_weight = 0
            
        return {
            'total_weight': self.total_weight_var.get(),
            'pallet_weight': self.pallet_weight_var.get(),
            'extra_weight': self.extra_weight_var.get(),
            'net_weight': f"{net_weight:.1f}",
            'weight': f"{net_weight:.1f}",  # 라벨에 표시될 무게 (순수무게)
            'date': self.date_var.get(),
            'printer': self.printer_var.get(),
            'product_name': '제품',  # 기본값
            'copies': self.copies_var.get() if hasattr(self, 'copies_var') else "1"
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
            copies = int(data.get('copies', self.default_label_copies) or self.default_label_copies)
            if copies < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("오류", "인쇄 매수는 1 이상의 정수여야 합니다.")
            return False
        data['copies'] = str(copies)
        
        try:
            total_weight = float(data['total_weight'])
            pallet_weight = float(data['pallet_weight'])
            extra_weight = float(data.get('extra_weight', self.extra_weight) or self.extra_weight)
            if extra_weight < 0:
                messagebox.showerror("오류", "기타 무게는 0 이상이어야 합니다.")
                return False
            
            if total_weight <= 0:
                messagebox.showerror("오류", "총무게는 0보다 큰 값이어야 합니다.")
                return False
                
            if pallet_weight < 0:
                messagebox.showerror("오류", "팔렛무게는 0 이상이어야 합니다.")
                return False
                
            if pallet_weight + extra_weight >= total_weight:
                messagebox.showerror("오류", "팔렛무게와 기타 무게 합은 총무게보다 작아야 합니다.")
                return False
                data['extra_weight'] = f"{extra_weight:g}"
                
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
            extra_weight = data.get('extra_weight', "0") or "0"
            try:
                total_val = float(total_weight)
            except ValueError:
                total_val = 0
            try:
                pallet_val = float(pallet_weight)
            except ValueError:
                pallet_val = 0
            try:
                extra_val = float(extra_weight)
            except ValueError:
                extra_val = 0
            net_weight = total_val - pallet_val - extra_val
            
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
            copies = self.default_label_copies
            try:
                copies = int(data.get('copies', self.default_label_copies) or self.default_label_copies)
            except (ValueError, TypeError):
                copies = self.default_label_copies
            if copies < 1:
                copies = self.default_label_copies
            
            success = True
            for copy_idx in range(copies):
                if not self.printer.print_image(
                    temp_img_path,
                    actual_printer_name,
                    label_width_cm=self.label_width_cm,
                    label_height_cm=self.label_height_cm
                ):
                    success = False
                    break
            
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
                
                # 양식 기록 옵션 제공 - 인라인 양식에 자동 입력
                response = messagebox.askyesno("양식 기록", "Daily Bulk Production Sheet 양식의 Total KG에 자동 입력하시겠습니까?")
                if response:
                    net_weight = data.get('net_weight', '')
                    if net_weight and hasattr(self, 'table_data_inline'):
                        # 첫 번째 빈 행에 Total KG 입력 (순수무게)
                        for row_data in self.table_data_inline:
                            if not row_data['total_kg'].get():
                                row_data['total_kg'].set(net_weight)
                                break
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
            selected_display = None
            if self.default_printer_name:
                for display_name, actual_name in self.printer_names.items():
                    if actual_name == self.default_printer_name:
                        selected_display = display_name
                        break
            if not selected_display:
                current_value = self.printer_var.get()
                if current_value in printer_list:
                    selected_display = current_value
            if not selected_display:
                selected_display = printer_list[0]
                actual = self.printer_names.get(selected_display)
                if actual:
                    self.default_printer_name = actual
                    self.save_settings()
            self.printer_var.set(selected_display)
            try:
                index = printer_list.index(selected_display)
                self.printer_combo.current(index)
            except ValueError:
                self.printer_combo.set(selected_display)
    
    def on_printer_selected(self, event=None):
        """프린터 선택 변경 시 기본 프린터 저장"""
        display_name = self.printer_var.get()
        actual_name = self.printer_names.get(display_name)
        if actual_name and actual_name != self.default_printer_name:
            self.default_printer_name = actual_name
            self.save_settings()
    
    def save_print_record(self, data):
        """인쇄 기록 저장"""
        record = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_weight': data['total_weight'],
            'pallet_weight': data['pallet_weight'],
            'net_weight': data['net_weight'],
            'printer': data['printer'],
            'date': data['date'],
            'copies': data.get('copies', str(self.default_label_copies))
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
            copies_str = record.get('copies', str(self.default_label_copies))
            display_text = f"{record['timestamp']} | 총:{record['total_weight']}kg 팔렛:{record['pallet_weight']}kg 순수:{record['net_weight']}kg | {record['printer']} | 매수:{copies_str}"
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
                    extra_weight = float(data.get('extra_weight', self.extra_weight) or self.extra_weight)
                    net_weight = total_weight - pallet_weight - extra_weight
                    
                    if net_weight <= 0:
                        return jsonify({
                            'success': False,
                            'error': 'INVALID_WEIGHT',
                            'message': '팔렛무게와 기타 무게의 합이 총무게보다 크거나 같습니다.'
                        }), 400
                        
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': 'INVALID_WEIGHT_FORMAT',
                        'message': '무게는 숫자여야 합니다.'
                    }), 400
                
                try:
                    copies = int(data.get('copies', self.default_label_copies) or self.default_label_copies)
                    if copies < 1:
                        raise ValueError
                except (ValueError, TypeError):
                    return jsonify({
                        'success': False,
                        'error': 'INVALID_COPIES',
                        'message': '인쇄 매수는 1 이상의 정수여야 합니다.'
                    }), 400
                
                data['copies'] = str(copies)
                
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
                extra_weight_str = data.get('extra_weight', '0')
                try:
                    total_val = float(total_weight_str)
                except ValueError:
                    total_val = 0
                try:
                    pallet_val = float(pallet_weight_str)
                except ValueError:
                    pallet_val = 0
                try:
                    extra_val = float(extra_weight_str)
                except ValueError:
                    extra_val = 0
                net_weight = total_val - pallet_val - extra_val
                
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
                success = True
                for copy_idx in range(copies):
                    if not self.printer.print_image(
                        temp_img_path,
                        actual_printer_name,
                        label_width_cm=self.label_width_cm,
                        label_height_cm=self.label_height_cm
                    ):
                        success = False
                        break
                
                # 임시 파일 삭제
                try:
                    os.remove(temp_img_path)
                except:
                    pass
                
                if success:
                    # 인쇄 기록 저장
                    self.save_print_record(data)
                    
                    # 양식 테이블에 Total KG 자동 입력 (모바일 전송)
                    # GUI 스레드에서 실행되도록 root.after 사용
                    try:
                        self.root.after(0, lambda: self.add_to_production_form(data))
                    except:
                        # root가 없을 경우 직접 호출
                        self.add_to_production_form(data)
                    
                    return jsonify({
                        'success': True,
                        'message': '라벨이 성공적으로 인쇄되었습니다.',
                        'data': {
                            'total_weight': data.get('total_weight'),
                            'pallet_weight': data.get('pallet_weight'),
                            'net_weight': data.get('net_weight'),
                            'printer': data.get('printer'),
                        'extra_weight': data.get('extra_weight'),
                            'copies': copies,
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
        
    def open_production_form(self):
        """Daily Bulk Production Sheet 양식 창 열기"""
        form_window = tk.Toplevel(self.root)
        form_window.title("Daily Bulk Production Sheet")
        form_window.geometry("800x900")
        form_window.resizable(True, True)
        
        # 스크롤 가능한 프레임
        canvas = tk.Canvas(form_window)
        scrollbar = ttk.Scrollbar(form_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 양식 입력 필드들
        form_data = {}
        
        # 제목
        title_label = ttk.Label(scrollable_frame, text="Daily Bulk Production Sheet", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # DATE
        ttk.Label(scrollable_frame, text="DATE:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        date_entry = ttk.Entry(scrollable_frame, textvariable=date_var, width=30)
        date_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        form_data['date'] = date_var
        
        # SHIFT
        ttk.Label(scrollable_frame, text="SHIFT:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        shift_var = tk.StringVar(value="AM")
        shift_frame = ttk.Frame(scrollable_frame)
        shift_frame.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        ttk.Radiobutton(shift_frame, text="AM", variable=shift_var, value="AM").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(shift_frame, text="PM", variable=shift_var, value="PM").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(shift_frame, text="Graveyard", variable=shift_var, value="Graveyard").pack(side=tk.LEFT, padx=5)
        form_data['shift'] = shift_var
        
        # Supervisor Name
        ttk.Label(scrollable_frame, text="Supervisor Name:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        supervisor_var = tk.StringVar()
        supervisor_entry = ttk.Entry(scrollable_frame, textvariable=supervisor_var, width=30)
        supervisor_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        form_data['supervisor_name'] = supervisor_var
        
        # Employee Name
        ttk.Label(scrollable_frame, text="Employee Name:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=2)
        employee_var = tk.StringVar()
        employee_entry = ttk.Entry(scrollable_frame, textvariable=employee_var, width=30)
        employee_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        form_data['employee_name'] = employee_var
        
        # Product Name
        ttk.Label(scrollable_frame, text="Product Name:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=2)
        product_var = tk.StringVar()
        product_entry = ttk.Entry(scrollable_frame, textvariable=product_var, width=30)
        product_entry.grid(row=5, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        form_data['product_name'] = product_var
        
        # Bulk Lot Code
        ttk.Label(scrollable_frame, text="Bulk Lot Code:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=2)
        bulk_lot_var = tk.StringVar()
        bulk_lot_entry = ttk.Entry(scrollable_frame, textvariable=bulk_lot_var, width=30)
        bulk_lot_entry.grid(row=6, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        form_data['bulk_lot_code'] = bulk_lot_var
        
        # Parchment Paper
        ttk.Label(scrollable_frame, text="Parchment Paper:").grid(row=7, column=0, sticky=tk.W, padx=5, pady=2)
        parchment_frame = ttk.Frame(scrollable_frame)
        parchment_frame.grid(row=7, column=1, sticky=tk.W, padx=5, pady=2)
        parchment_reuse_var = tk.BooleanVar()
        ttk.Checkbutton(parchment_frame, text="Reuse", variable=parchment_reuse_var).pack(side=tk.LEFT, padx=5)
        ttk.Label(parchment_frame, text="or Lot code:").pack(side=tk.LEFT, padx=5)
        parchment_lot_var = tk.StringVar()
        parchment_lot_entry = ttk.Entry(parchment_frame, textvariable=parchment_lot_var, width=20)
        parchment_lot_entry.pack(side=tk.LEFT, padx=5)
        form_data['parchment_reuse'] = parchment_reuse_var
        form_data['parchment_lot_code'] = parchment_lot_var
        
        # Quantity
        ttk.Label(scrollable_frame, text="Quantity:").grid(row=8, column=0, sticky=tk.W, padx=5, pady=2)
        quantity_var = tk.StringVar()
        quantity_entry = ttk.Entry(scrollable_frame, textvariable=quantity_var, width=30)
        quantity_entry.grid(row=8, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        form_data['quantity'] = quantity_var
        
        # Quality Checked
        ttk.Label(scrollable_frame, text="Quality Checked (Supervisor Initial):").grid(row=9, column=0, sticky=tk.W, padx=5, pady=2)
        quality_var = tk.StringVar()
        quality_entry = ttk.Entry(scrollable_frame, textvariable=quality_var, width=30)
        quality_entry.grid(row=9, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        form_data['quality_checked'] = quality_var
        
        # Production Data Table
        table_label = ttk.Label(scrollable_frame, text="Production Data Table", font=("Arial", 12, "bold"))
        table_label.grid(row=10, column=0, columnspan=2, pady=(10, 5))
        
        # 테이블 헤더
        headers = ["Bulk Plastic Bag\nLot Codes", "Bulk Bag\nQTY", "Pallet #", "Total KG", "Notes", "Initial"]
        for col, header in enumerate(headers):
            ttk.Label(scrollable_frame, text=header, font=("Arial", 9, "bold"), borderwidth=1, relief=tk.SOLID).grid(
                row=11, column=col, sticky=(tk.W, tk.E), padx=1, pady=1)
        
        # 테이블 행 (10개 행)
        table_data = []
        header_keys = ['bulk_plastic_bag_lot_codes', 'bulk_bag_qty', 'pallet_num', 'total_kg', 'notes', 'initial']
        for row in range(10):
            row_data = {}
            for col, key in enumerate(header_keys):
                var = tk.StringVar()
                entry = ttk.Entry(scrollable_frame, textvariable=var, width=15)
                entry.grid(row=12+row, column=col, sticky=(tk.W, tk.E), padx=1, pady=1)
                row_data[key] = var
            table_data.append(row_data)
        form_data['production_table'] = table_data
        
        # Production Notes
        ttk.Label(scrollable_frame, text="Production Notes:").grid(row=22, column=0, sticky=(tk.W, tk.N), padx=5, pady=2)
        notes_text = tk.Text(scrollable_frame, height=5, width=50)
        notes_text.grid(row=22, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        form_data['production_notes'] = notes_text
        
        # Verified by QA
        ttk.Label(scrollable_frame, text="Verified by QA:").grid(row=23, column=0, sticky=tk.W, padx=5, pady=2)
        qa_var = tk.StringVar()
        qa_entry = ttk.Entry(scrollable_frame, textvariable=qa_var, width=30)
        qa_entry.grid(row=23, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        form_data['verified_by_qa'] = qa_var
        
        # Supervisor Name & Signature
        ttk.Label(scrollable_frame, text="Supervisor Name & Signature:").grid(row=24, column=0, sticky=tk.W, padx=5, pady=2)
        supervisor_sig_var = tk.StringVar()
        supervisor_sig_entry = ttk.Entry(scrollable_frame, textvariable=supervisor_sig_var, width=30)
        supervisor_sig_entry.grid(row=24, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        form_data['supervisor_signature'] = supervisor_sig_var
        
        # 그리드 가중치 설정
        scrollable_frame.columnconfigure(1, weight=1)
        for col in range(6):
            scrollable_frame.columnconfigure(col, weight=1)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 버튼 프레임
        button_frame = ttk.Frame(form_window)
        button_frame.pack(pady=10)
        
        def save_form():
            """양식 데이터 저장"""
            record = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'date': form_data['date'].get(),
                'shift': form_data['shift'].get(),
                'supervisor_name': form_data['supervisor_name'].get(),
                'employee_name': form_data['employee_name'].get(),
                'product_name': form_data['product_name'].get(),
                'bulk_lot_code': form_data['bulk_lot_code'].get(),
                'parchment_reuse': form_data['parchment_reuse'].get(),
                'parchment_lot_code': form_data['parchment_lot_code'].get(),
                'quantity': form_data['quantity'].get(),
                'quality_checked': form_data['quality_checked'].get(),
                'production_table': [
                    {
                        'bulk_plastic_bag_lot_codes': row['bulk_plastic_bag_lot_codes'].get(),
                        'bulk_bag_qty': row['bulk_bag_qty'].get(),
                        'pallet_num': row['pallet_num'].get(),
                        'total_kg': row['total_kg'].get(),
                        'notes': row['notes'].get(),
                        'initial': row['initial'].get()
                    }
                    for row in table_data
                ],
                'production_notes': form_data['production_notes'].get('1.0', tk.END).strip(),
                'verified_by_qa': form_data['verified_by_qa'].get(),
                'supervisor_signature': form_data['supervisor_signature'].get()
            }
            
            self.production_records.append(record)
            self.save_production_records()
            messagebox.showinfo("성공", "양식이 저장되었습니다.")
            form_window.destroy()
        
        # 라벨 인쇄 시 자동으로 TOTAL KG에 입력하기 위한 함수
        def fill_from_label():
            """현재 라벨 데이터를 양식의 TOTAL KG에 자동 입력 (순수무게)"""
            label_data = self.get_label_data()
            net_weight = label_data.get('net_weight', '')
            
            if net_weight:
                # 첫 번째 빈 행에 Total KG 입력 (순수무게)
                for row_data in table_data:
                    if not row_data['total_kg'].get():
                        row_data['total_kg'].set(net_weight)
                        break
        
        ttk.Button(button_frame, text="라벨 데이터 가져오기", command=fill_from_label).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="저장", command=save_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="취소", command=form_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def open_production_form_with_data(self, label_data):
        """라벨 데이터를 포함하여 Daily Bulk Production Sheet 양식 창 열기"""
        form_window = tk.Toplevel(self.root)
        form_window.title("Daily Bulk Production Sheet")
        form_window.geometry("800x900")
        form_window.resizable(True, True)
        
        # 스크롤 가능한 프레임
        canvas = tk.Canvas(form_window)
        scrollbar = ttk.Scrollbar(form_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 양식 입력 필드들
        form_data = {}
        
        # 제목
        title_label = ttk.Label(scrollable_frame, text="Daily Bulk Production Sheet", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # DATE
        ttk.Label(scrollable_frame, text="DATE:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        date_var = tk.StringVar(value=label_data.get('date', datetime.now().strftime('%Y-%m-%d')))
        date_entry = ttk.Entry(scrollable_frame, textvariable=date_var, width=30)
        date_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        form_data['date'] = date_var
        
        # SHIFT
        ttk.Label(scrollable_frame, text="SHIFT:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        shift_var = tk.StringVar(value="AM")
        shift_frame = ttk.Frame(scrollable_frame)
        shift_frame.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        ttk.Radiobutton(shift_frame, text="AM", variable=shift_var, value="AM").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(shift_frame, text="PM", variable=shift_var, value="PM").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(shift_frame, text="Graveyard", variable=shift_var, value="Graveyard").pack(side=tk.LEFT, padx=5)
        form_data['shift'] = shift_var
        
        # Supervisor Name
        ttk.Label(scrollable_frame, text="Supervisor Name:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        supervisor_var = tk.StringVar()
        supervisor_entry = ttk.Entry(scrollable_frame, textvariable=supervisor_var, width=30)
        supervisor_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        form_data['supervisor_name'] = supervisor_var
        
        # Employee Name
        ttk.Label(scrollable_frame, text="Employee Name:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=2)
        employee_var = tk.StringVar()
        employee_entry = ttk.Entry(scrollable_frame, textvariable=employee_var, width=30)
        employee_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        form_data['employee_name'] = employee_var
        
        # Product Name
        ttk.Label(scrollable_frame, text="Product Name:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=2)
        product_var = tk.StringVar()
        product_entry = ttk.Entry(scrollable_frame, textvariable=product_var, width=30)
        product_entry.grid(row=5, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        form_data['product_name'] = product_var
        
        # Bulk Lot Code
        ttk.Label(scrollable_frame, text="Bulk Lot Code:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=2)
        bulk_lot_var = tk.StringVar()
        bulk_lot_entry = ttk.Entry(scrollable_frame, textvariable=bulk_lot_var, width=30)
        bulk_lot_entry.grid(row=6, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        form_data['bulk_lot_code'] = bulk_lot_var
        
        # Parchment Paper
        ttk.Label(scrollable_frame, text="Parchment Paper:").grid(row=7, column=0, sticky=tk.W, padx=5, pady=2)
        parchment_frame = ttk.Frame(scrollable_frame)
        parchment_frame.grid(row=7, column=1, sticky=tk.W, padx=5, pady=2)
        parchment_reuse_var = tk.BooleanVar()
        ttk.Checkbutton(parchment_frame, text="Reuse", variable=parchment_reuse_var).pack(side=tk.LEFT, padx=5)
        ttk.Label(parchment_frame, text="or Lot code:").pack(side=tk.LEFT, padx=5)
        parchment_lot_var = tk.StringVar()
        parchment_lot_entry = ttk.Entry(parchment_frame, textvariable=parchment_lot_var, width=20)
        parchment_lot_entry.pack(side=tk.LEFT, padx=5)
        form_data['parchment_reuse'] = parchment_reuse_var
        form_data['parchment_lot_code'] = parchment_lot_var
        
        # Quantity
        ttk.Label(scrollable_frame, text="Quantity:").grid(row=8, column=0, sticky=tk.W, padx=5, pady=2)
        quantity_var = tk.StringVar()
        quantity_entry = ttk.Entry(scrollable_frame, textvariable=quantity_var, width=30)
        quantity_entry.grid(row=8, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        form_data['quantity'] = quantity_var
        
        # Quality Checked
        ttk.Label(scrollable_frame, text="Quality Checked (Supervisor Initial):").grid(row=9, column=0, sticky=tk.W, padx=5, pady=2)
        quality_var = tk.StringVar()
        quality_entry = ttk.Entry(scrollable_frame, textvariable=quality_var, width=30)
        quality_entry.grid(row=9, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        form_data['quality_checked'] = quality_var
        
        # Production Data Table
        table_label = ttk.Label(scrollable_frame, text="Production Data Table", font=("Arial", 12, "bold"))
        table_label.grid(row=10, column=0, columnspan=2, pady=(10, 5))
        
        # 테이블 헤더
        headers = ["Bulk Plastic Bag\nLot Codes", "Bulk Bag\nQTY", "Pallet #", "Total KG", "Notes", "Initial"]
        for col, header in enumerate(headers):
            ttk.Label(scrollable_frame, text=header, font=("Arial", 9, "bold"), borderwidth=1, relief=tk.SOLID).grid(
                row=11, column=col, sticky=(tk.W, tk.E), padx=1, pady=1)
        
        # 테이블 행 (10개 행)
        table_data = []
        header_keys = ['bulk_plastic_bag_lot_codes', 'bulk_bag_qty', 'pallet_num', 'total_kg', 'notes', 'initial']
        for row in range(10):
            row_data = {}
            for col, key in enumerate(header_keys):
                var = tk.StringVar()
                entry = ttk.Entry(scrollable_frame, textvariable=var, width=15)
                entry.grid(row=12+row, column=col, sticky=(tk.W, tk.E), padx=1, pady=1)
                row_data[key] = var
            table_data.append(row_data)
        form_data['production_table'] = table_data
        
        # 라벨 데이터에서 TOTAL KG 자동 입력 (첫 번째 빈 행, 순수무게)
        net_weight = label_data.get('net_weight', '')
        if net_weight:
            try:
                table_data[0]['total_kg'].set(net_weight)
            except:
                pass
        
        # Production Notes
        ttk.Label(scrollable_frame, text="Production Notes:").grid(row=22, column=0, sticky=(tk.W, tk.N), padx=5, pady=2)
        notes_text = tk.Text(scrollable_frame, height=5, width=50)
        notes_text.grid(row=22, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        form_data['production_notes'] = notes_text
        
        # Verified by QA
        ttk.Label(scrollable_frame, text="Verified by QA:").grid(row=23, column=0, sticky=tk.W, padx=5, pady=2)
        qa_var = tk.StringVar()
        qa_entry = ttk.Entry(scrollable_frame, textvariable=qa_var, width=30)
        qa_entry.grid(row=23, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        form_data['verified_by_qa'] = qa_var
        
        # Supervisor Name & Signature
        ttk.Label(scrollable_frame, text="Supervisor Name & Signature:").grid(row=24, column=0, sticky=tk.W, padx=5, pady=2)
        supervisor_sig_var = tk.StringVar()
        supervisor_sig_entry = ttk.Entry(scrollable_frame, textvariable=supervisor_sig_var, width=30)
        supervisor_sig_entry.grid(row=24, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        form_data['supervisor_signature'] = supervisor_sig_var
        
        # 그리드 가중치 설정
        scrollable_frame.columnconfigure(1, weight=1)
        for col in range(6):
            scrollable_frame.columnconfigure(col, weight=1)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 버튼 프레임
        button_frame = ttk.Frame(form_window)
        button_frame.pack(pady=10)
        
        def save_form():
            """양식 데이터 저장"""
            record = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'date': form_data['date'].get(),
                'shift': form_data['shift'].get(),
                'supervisor_name': form_data['supervisor_name'].get(),
                'employee_name': form_data['employee_name'].get(),
                'product_name': form_data['product_name'].get(),
                'bulk_lot_code': form_data['bulk_lot_code'].get(),
                'parchment_reuse': form_data['parchment_reuse'].get(),
                'parchment_lot_code': form_data['parchment_lot_code'].get(),
                'quantity': form_data['quantity'].get(),
                'quality_checked': form_data['quality_checked'].get(),
                'production_table': [
                    {
                        'bulk_plastic_bag_lot_codes': row['bulk_plastic_bag_lot_codes'].get(),
                        'bulk_bag_qty': row['bulk_bag_qty'].get(),
                        'pallet_num': row['pallet_num'].get(),
                        'total_kg': row['total_kg'].get(),
                        'notes': row['notes'].get(),
                        'initial': row['initial'].get()
                    }
                    for row in table_data
                ],
                'production_notes': form_data['production_notes'].get('1.0', tk.END).strip(),
                'verified_by_qa': form_data['verified_by_qa'].get(),
                'supervisor_signature': form_data['supervisor_signature'].get(),
                'label_data': label_data  # 라벨 데이터도 함께 저장
            }
            
            self.production_records.append(record)
            self.save_production_records()
            messagebox.showinfo("성공", "양식이 저장되었습니다.")
            form_window.destroy()
        
        def fill_from_label():
            """현재 라벨 데이터를 양식의 TOTAL KG에 자동 입력 (순수무게)"""
            label_data = self.get_label_data()
            net_weight = label_data.get('net_weight', '')
            
            if net_weight:
                # 첫 번째 빈 행에 Total KG 입력 (순수무게)
                for row_data in table_data:
                    if not row_data['total_kg'].get():
                        row_data['total_kg'].set(net_weight)
                        break
        
        ttk.Button(button_frame, text="라벨 데이터 가져오기", command=fill_from_label).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="저장", command=save_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="취소", command=form_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def load_production_records(self):
        """저장된 양식 데이터 로드"""
        try:
            records_file = "production_records.json"
            if os.path.exists(records_file):
                with open(records_file, 'r', encoding='utf-8') as f:
                    self.production_records = json.load(f)
        except Exception as e:
            print(f"양식 데이터 로드 실패: {e}")
            self.production_records = []
    
    def save_production_records(self):
        """양식 데이터를 JSON 파일로 저장"""
        try:
            records_file = "production_records.json"
            with open(records_file, 'w', encoding='utf-8') as f:
                json.dump(self.production_records, f, ensure_ascii=False, indent=2)
            print(f"양식 데이터 저장 완료: {len(self.production_records)}개 기록")
        except Exception as e:
            print(f"양식 데이터 저장 실패: {e}")
    
    def load_saved_bulk_sheet(self):
        """저장된 양식 목록을 보여주고 선택해서 불러오기"""
        if not self.production_records:
            messagebox.showinfo("알림", "저장된 양식이 없습니다.")
            return
        
        # 새 창 열기
        load_window = tk.Toplevel(self.root)
        load_window.title("저장된 양식 불러오기")
        load_window.geometry("600x400")
        
        # 제목 라벨
        title_label = ttk.Label(load_window, text="저장된 양식 목록", font=("Arial", 12, "bold"))
        title_label.pack(pady=10)
        
        # 리스트박스와 스크롤바
        list_frame = ttk.Frame(load_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Arial", 10))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        # 제목 생성 및 리스트에 추가 (date + product name + shift)
        for idx, record in enumerate(self.production_records):
            date = record.get('date', '날짜 없음')
            product = record.get('product_name', '제품명 없음')
            shift = record.get('shift', 'Shift 없음')
            title = f"{date} - {product} - {shift}"
            listbox.insert(tk.END, title)
        
        # 버튼 프레임
        button_frame = ttk.Frame(load_window)
        button_frame.pack(pady=10)
        
        def load_selected():
            """선택한 양식 불러오기"""
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("경고", "양식을 선택해주세요.")
                return
            
            selected_idx = selection[0]
            record = self.production_records[selected_idx]
            
            # 폼에 데이터 채우기
            try:
                # 기본 필드 채우기
                if 'date' in record:
                    self.form_data_inline['date'].set(record['date'])
                if 'shift' in record:
                    self.form_data_inline['shift'].set(record['shift'])
                if 'supervisor_name' in record:
                    self.form_data_inline['supervisor_name'].set(record['supervisor_name'])
                if 'employee_name' in record:
                    self.form_data_inline['employee_name'].set(record['employee_name'])
                if 'product_name' in record:
                    self.form_data_inline['product_name'].set(record['product_name'])
                if 'bulk_lot_code' in record:
                    self.form_data_inline['bulk_lot_code'].set(record['bulk_lot_code'])
                if 'parchment_reuse' in record:
                    self.form_data_inline['parchment_reuse'].set(record['parchment_reuse'])
                if 'parchment_lot_code' in record:
                    self.form_data_inline['parchment_lot_code'].set(record['parchment_lot_code'])
                if 'no_choco_coating' in record:
                    self.form_data_inline['no_choco_coating'].set(record['no_choco_coating'])
                if 'quantity' in record:
                    self.form_data_inline['quantity'].set(record['quantity'])
                if 'quality_checked' in record:
                    self.form_data_inline['quality_checked'].set(record['quality_checked'])
                
                # production_table은 불러오지 않음
                
                messagebox.showinfo("성공", "양식이 불러와졌습니다.")
                load_window.destroy()
            except Exception as e:
                messagebox.showerror("오류", f"양식 불러오기 실패: {e}")
        
        def delete_selected():
            """선택한 양식 삭제"""
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("경고", "양식을 선택해주세요.")
                return
            
            if messagebox.askyesno("확인", "선택한 양식을 삭제하시겠습니까?"):
                selected_idx = selection[0]
                self.production_records.pop(selected_idx)
                self.save_production_records()
                listbox.delete(selection[0])
                messagebox.showinfo("성공", "양식이 삭제되었습니다.")
        
        ttk.Button(button_frame, text="불러오기", command=load_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="삭제", command=delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="취소", command=load_window.destroy).pack(side=tk.LEFT, padx=5)
        
        # 더블클릭으로 불러오기
        def on_double_click(event):
            load_selected()
        listbox.bind('<Double-Button-1>', on_double_click)

    def on_closing(self):
        """프로그램 종료 시"""
        self.server_running = False
        try:
            self.save_settings()
        except Exception:
            pass
        self.root.destroy()

def main():
    # 만료일 체크 (2026-06-30까지)
    try:
        expiry_date = datetime(2026, 6, 30, 23, 59, 59)
        current_date = datetime.now()
        
        if current_date > expiry_date:
            root = tk.Tk()
            root.withdraw()  # 메인 윈도우 숨기기
            messagebox.showerror(
                "원인 모를 오류가 발생했습니다.",
            )
            root.destroy()
            return
    except Exception as e:
        # 날짜 체크 중 오류 발생 시에도 프로그램 종료
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("오류", f"프로그램 초기화 중 오류가 발생했습니다: {e}")
        root.destroy()
        return
    
    root = tk.Tk()
    app = LabelPrinterGUI(root)
    
    # 종료 이벤트 처리
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    root.mainloop()

if __name__ == "__main__":
    main()
