from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black, red, blue
import os
import tempfile
import json
from datetime import datetime
import logging

app = Flask(__name__)
CORS(app)

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
        # 임시 PDF 파일 생성
        pdf_path = os.path.join(self.temp_dir, f"label_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        
        # PDF 캔버스 생성
        c = canvas.Canvas(pdf_path, pagesize=(LABEL_WIDTH, LABEL_HEIGHT))
        
        # 폰트 설정 (한글 지원을 위해 기본 폰트 사용)
        c.setFont("Helvetica-Bold", 16)
        
        # 배경 테두리 그리기
        c.rect(0.2*cm, 0.2*cm, LABEL_WIDTH-0.4*cm, LABEL_HEIGHT-0.4*cm)
        
        # 제품명 (상단)
        c.drawString(0.5*cm, LABEL_HEIGHT-1.2*cm, "제품 라벨")
        
        # 순수무게 계산 (total_weight, pallet_weight, extra_weight 사용)
        net_weight = None
        if 'net_weight' in data and data['net_weight']:
            try:
                net_weight = float(data['net_weight'])
            except (ValueError, TypeError):
                net_weight = None
        
        if net_weight is None:
            # net_weight가 없으면 계산
            total_weight = 0
            pallet_weight = 0
            extra_weight = 0
            
            try:
                if 'total_weight' in data and data['total_weight']:
                    total_weight = float(data['total_weight'])
            except (ValueError, TypeError):
                pass
            
            try:
                if 'pallet_weight' in data and data['pallet_weight']:
                    pallet_weight = float(data['pallet_weight'])
            except (ValueError, TypeError):
                pass
            
            try:
                if 'extra_weight' in data and data['extra_weight']:
                    extra_weight = float(data['extra_weight'])
            except (ValueError, TypeError):
                pass
            
            net_weight = total_weight - pallet_weight - extra_weight
        
        # 순수무게 (중앙, 가장 큰 글씨)
        if net_weight and net_weight > 0:
            c.setFont("Helvetica-Bold", 28)
            net_weight_text = f"{net_weight:.1f} kg"
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
        return pdf_path
    
    def create_bulk_production_sheet_pdf(self, data=None):
        """벌크 생산 시트 PDF 생성"""
        data = data or {}
        pdf_path = os.path.join(self.temp_dir, f"bulk_sheet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        
        c = canvas.Canvas(pdf_path, pagesize=BULK_SHEET_PAGE_SIZE)
        page_width, page_height = BULK_SHEET_PAGE_SIZE
        margin = 1.6 * cm
        
        # Header
        logo_y = page_height - margin
        c.setFont("Helvetica-Bold", 22)
        c.setFillColor(blue)
        c.drawString(margin, logo_y, "innofoods")
        
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(margin + 6.5 * cm, logo_y, "Daily Bulk Production Sheet")
        
        # Document info box
        doc_box_width = 7.0 * cm
        doc_box_height = 3.2 * cm
        doc_box_x = page_width - margin - doc_box_width
        doc_box_y = logo_y - doc_box_height + 0.6 * cm
        c.rect(doc_box_x, doc_box_y, doc_box_width, doc_box_height)
        c.setFont("Helvetica", 9)
        doc_info = [
            ("Document No:", "INNO-PROD-F-041"),
            ("Issue No:", "04"),
            ("Prepared By:", "Seon Lee"),
            ("Approved By:", "Jeff Chen"),
            ("Issue Date:", "Mar 13, 2023"),
            ("Review Date:", "Sep 14, 2023"),
        ]
        for idx, (label, value) in enumerate(doc_info):
            text_y = doc_box_y + doc_box_height - 0.55 * cm - idx * 0.55 * cm
            c.drawString(doc_box_x + 0.35 * cm, text_y, f"{label} {value}")
        
        # Top form fields
        form_top = logo_y - 1.6 * cm
        line_length = 7.2 * cm
        right_field_width = 7.4 * cm
        c.setFont("Helvetica", 11)
        
        def draw_field(label, x, y, width, value_text=""):
            c.drawString(x, y, label)
            line_start = x + c.stringWidth(label, "Helvetica", 11) + 6
            line_end = line_start + width
            c.line(line_start, y - 2, line_end, y - 2)
            if value_text:
                c.drawString(line_start + 2, y - 12, value_text)
        
        draw_field("DATE:", margin, form_top, line_length, data.get("date", ""))
        draw_field("Supervisor Name:", margin, form_top - 1.0 * cm, line_length, data.get("supervisor_name", ""))
        draw_field("Product Name:", margin, form_top - 2.0 * cm, line_length, data.get("product_name", ""))
        
        # Parchment paper section
        parchment_y = form_top - 3.0 * cm
        c.drawString(margin, parchment_y, "Parchment Paper: Reuse")
        checkbox_size = 0.5 * cm
        checkbox_x = margin + c.stringWidth("Parchment Paper: Reuse", "Helvetica", 11) + 8
        c.rect(checkbox_x, parchment_y - 8, checkbox_size, checkbox_size)
        c.drawString(checkbox_x + checkbox_size + 6, parchment_y, "or Lot code:")
        lot_code_line_start = checkbox_x + checkbox_size + 6 + c.stringWidth("or Lot code:", "Helvetica", 11) + 6
        c.line(lot_code_line_start, parchment_y - 2, lot_code_line_start + 6.0 * cm, parchment_y - 2)
        if data.get("parchment_lot_code"):
            c.drawString(lot_code_line_start + 4, parchment_y - 12, data["parchment_lot_code"])
        
        # Right column fields
        right_x = margin + line_length + 1.5 * cm
        draw_field("SHIFT (circle one):", right_x, form_top, right_field_width, data.get("shift", ""))
        c.setFont("Helvetica", 10)
        c.drawString(right_x + 4.0 * cm, form_top, "AM / PM / Graveyard")
        c.setFont("Helvetica", 11)
        draw_field("Employee Name:", right_x, form_top - 1.0 * cm, right_field_width, data.get("employee_name", ""))
        draw_field("Bulk Lot Code:", right_x, form_top - 2.0 * cm, right_field_width, data.get("bulk_lot_code", ""))
        draw_field("Quantity:", right_x, form_top - 3.0 * cm, right_field_width, data.get("quantity", ""))
        
        # Quality check line
        qc_y = parchment_y - 1.1 * cm
        c.setFont("Helvetica", 11)
        c.drawString(margin, qc_y, "Quality Checked (e.g. color, texture, crumb, taste) - Supervisor Initial:")
        c.line(margin, qc_y - 4, page_width - margin, qc_y - 4)
        
        # Main table
        table_top = qc_y - 0.9 * cm
        table_left = margin
        table_width = page_width - 2 * margin
        header_height = 1.4 * cm
        body_row_height = 1.2 * cm
        body_rows = 12
        table_height = header_height + body_rows * body_row_height
        table_bottom = table_top - table_height
        
        c.rect(table_left, table_bottom, table_width, table_height)
        
        column_specs = [
            ("Bulk Plastic Bag Lot Codes", 0.3),
            ("Bulk Bag QTY", 0.12),
            ("Pallet #", 0.12),
            ("Total KG", 0.12),
            ("Notes", 0.26),
            ("Initial", 0.08),
        ]
        
        # Column vertical lines and headers
        x_positions = [table_left]
        for _, ratio in column_specs:
            x_positions.append(x_positions[-1] + ratio * table_width)
        for x in x_positions[1:-1]:
            c.line(x, table_bottom, x, table_top)
        c.line(table_left, table_top - header_height, table_left + table_width, table_top - header_height)
        
        c.setFont("Helvetica-Bold", 11)
        header_y = table_top - 0.5 * cm
        for idx, (title, _) in enumerate(column_specs):
            text_x = x_positions[idx] + 0.3 * cm
            c.drawString(text_x, header_y, title)
        
        # Body horizontal lines
        c.setFont("Helvetica", 10)
        for row in range(body_rows):
            y = table_top - header_height - row * body_row_height
            c.line(table_left, y, table_left + table_width, y)
        
        # Production notes section
        notes_top = table_bottom - 1.2 * cm
        notes_height = 3.0 * cm
        c.drawString(margin, notes_top, "Production Notes:")
        c.rect(margin, notes_top - notes_height, table_width, notes_height)
        
        # Sign-off section
        sign_y = notes_top - notes_height - 1.0 * cm
        c.drawString(margin, sign_y, "Verified by QA:")
        c.line(margin + 4.0 * cm, sign_y - 2, margin + 4.0 * cm + 6.6 * cm, sign_y - 2)
        
        supervisor_x = margin + 11.5 * cm
        c.drawString(supervisor_x, sign_y, "Supervisor Name & Signature:")
        c.line(supervisor_x + 6.0 * cm, sign_y - 2, supervisor_x + 6.0 * cm + 7.6 * cm, sign_y - 2)
        
        date_x = margin + table_width - 5.5 * cm
        c.drawString(date_x, sign_y, "Date:")
        c.line(date_x + 1.3 * cm, sign_y - 2, date_x + 1.3 * cm + 4.2 * cm, sign_y - 2)
        
        c.setFont("Helvetica", 9)
        c.drawRightString(page_width - margin, margin - 0.4 * cm, "Page 1")
        c.drawString(margin, margin - 0.4 * cm, "Inno Foods Inc.")
        
        c.save()
        return pdf_path
    
    def print_label(self, pdf_path, printer_name=None):
        """라벨 인쇄"""
        try:
            # CUPS를 통한 인쇄 (Linux/macOS)
            if os.name == 'posix':
                import subprocess
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
                # Windows의 경우
                os.startfile(pdf_path, "print")
                return True
        except Exception as e:
            logger.error(f"인쇄 중 오류 발생: {str(e)}")
            return False

# 전역 프린터 인스턴스
printer = LabelPrinter()

@app.route('/')
def index():
    """메인 페이지"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>라벨 인쇄 서버</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 900px; margin: 0 auto; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            button { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background-color: #0056b3; }
            .preview { border: 1px solid #ccc; padding: 20px; margin: 20px 0; background: white; }
            .card { border: 1px solid #eee; border-radius: 6px; padding: 20px; margin-bottom: 30px; box-shadow: 0 1px 4px rgba(0,0,0,0.05); }
            .card h2 { margin-top: 0; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; }
            .actions { margin-top: 10px; display: flex; gap: 10px; flex-wrap: wrap; }
            .secondary { background-color: #6c757d; }
            .secondary:hover { background-color: #545b62; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>라벨 & 벌크 생산 시트 인쇄</h1>
            <p>라벨(10cm x 5cm)과 Daily Bulk Production Sheet(A4)를 인쇄할 수 있습니다.</p>
            
            <div class="card">
                <h2>라벨 인쇄</h2>
                <form id="labelForm">
                    <div class="grid">
                        <div class="form-group">
                            <label for="product_name">제품명:</label>
                            <input type="text" id="product_name" name="product_name" placeholder="제품명을 입력하세요">
                        </div>
                        
                        <div class="form-group">
                            <label for="weight">무게 (kg):</label>
                            <input type="number" id="weight" name="weight" step="0.1" placeholder="무게를 입력하세요">
                        </div>
                        
                        <div class="form-group">
                            <label for="date">날짜:</label>
                            <input type="date" id="date" name="date">
                        </div>
                        
                        <div class="form-group">
                            <label for="barcode">바코드/ID:</label>
                            <input type="text" id="barcode" name="barcode" placeholder="바코드 또는 ID">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="additional_info">추가 정보:</label>
                        <textarea id="additional_info" name="additional_info" rows="2" placeholder="추가 정보를 입력하세요"></textarea>
                    </div>
                    
                    <div class="actions">
                        <button type="submit">라벨 인쇄</button>
                    </div>
                </form>
            </div>
            
            <div class="card">
                <h2>Daily Bulk Production Sheet 인쇄</h2>
                <form id="bulkSheetForm">
                    <div class="grid">
                        <div class="form-group">
                            <label for="bulk_date">DATE</label>
                            <input type="date" id="bulk_date" name="date">
                        </div>
                        <div class="form-group">
                            <label for="bulk_shift">SHIFT (AM / PM / Graveyard)</label>
                            <input type="text" id="bulk_shift" name="shift" placeholder="예: AM">
                        </div>
                        <div class="form-group">
                            <label for="bulk_supervisor">Supervisor Name</label>
                            <input type="text" id="bulk_supervisor" name="supervisor_name">
                        </div>
                        <div class="form-group">
                            <label for="bulk_employee">Employee Name</label>
                            <input type="text" id="bulk_employee" name="employee_name">
                        </div>
                        <div class="form-group">
                            <label for="bulk_product_name">Product Name</label>
                            <input type="text" id="bulk_product_name" name="product_name">
                        </div>
                        <div class="form-group">
                            <label for="bulk_lot_code">Bulk Lot Code</label>
                            <input type="text" id="bulk_lot_code" name="bulk_lot_code">
                        </div>
                        <div class="form-group">
                            <label for="bulk_quantity">Quantity</label>
                            <input type="text" id="bulk_quantity" name="quantity">
                        </div>
                        <div class="form-group">
                            <label for="bulk_parchment_lot">Parchment Paper Lot Code</label>
                            <input type="text" id="bulk_parchment_lot" name="parchment_lot_code">
                        </div>
                    </div>
                    
                    <div class="actions">
                        <button type="button" id="bulkPreviewBtn" class="secondary">미리보기</button>
                        <button type="submit" id="bulkPrintBtn">벌크 생산 시트 인쇄</button>
                    </div>
                </form>
            </div>
            
            <div id="result"></div>
        </div>
        
        <script>
            document.getElementById('date').value = new Date().toISOString().split('T')[0];
            document.getElementById('bulk_date').value = new Date().toISOString().split('T')[0];
            
            document.getElementById('labelForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const formData = new FormData(this);
                const data = Object.fromEntries(formData);
                
                try {
                    const response = await fetch('/api/print', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    document.getElementById('result').innerHTML = 
                        '<div style="color: ' + (result.success ? 'green' : 'red') + '">' + 
                        result.message + '</div>';
                } catch (error) {
                    document.getElementById('result').innerHTML = 
                        '<div style="color: red">오류: ' + error.message + '</div>';
                }
            });
            
            const bulkForm = document.getElementById('bulkSheetForm');
            const bulkPreviewBtn = document.getElementById('bulkPreviewBtn');
            
            bulkForm.addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const formData = new FormData(bulkForm);
                const data = Object.fromEntries(formData);
                
                try {
                    const response = await fetch('/api/print/bulk-sheet', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    document.getElementById('result').innerHTML = 
                        '<div style="color: ' + (result.success ? 'green' : 'red') + '">' + 
                        result.message + '</div>';
                } catch (error) {
                    document.getElementById('result').innerHTML = 
                        '<div style="color: red">오류: ' + error.message + '</div>';
                }
            });
            
            bulkPreviewBtn.addEventListener('click', async function() {
                const formData = new FormData(bulkForm);
                const data = Object.fromEntries(formData);
                
                try {
                    const response = await fetch('/api/preview/bulk-sheet', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(data)
                    });
                    
                    if (!response.ok) {
                        const error = await response.json();
                        throw new Error(error.message || '미리보기 생성 실패');
                    }
                    
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    window.open(url, '_blank');
                } catch (error) {
                    document.getElementById('result').innerHTML = 
                        '<div style="color: red">오류: ' + error.message + '</div>';
                }
            });
        </script>
    </body>
    </html>
    """

@app.route('/api/print', methods=['POST'])
def print_label():
    """라벨 인쇄 API (모바일용)"""
    try:
        data = request.get_json()
        
        # 필수 데이터 검증 (total_weight와 pallet_weight 필요)
        if not data.get('total_weight') or not data.get('pallet_weight'):
            return jsonify({
                'success': False, 
                'error': 'WEIGHT_REQUIRED',
                'message': '총무게와 팔렛무게 정보가 필요합니다.'
            }), 400
        
        # 기본값 설정
        if not data.get('date'):
            data['date'] = datetime.now().strftime('%Y-%m-%d')
        
        if not data.get('extra_weight'):
            data['extra_weight'] = '0'
        
        # 순수무게 계산
        try:
            total_weight = float(data['total_weight'])
            pallet_weight = float(data['pallet_weight'])
            extra_weight = float(data.get('extra_weight', 0))
            net_weight = total_weight - pallet_weight - extra_weight
            
            if net_weight <= 0:
                return jsonify({
                    'success': False,
                    'error': 'INVALID_WEIGHT',
                    'message': '순수무게가 0 이하입니다. 무게를 확인해주세요.'
                }), 400
            
            data['net_weight'] = f"{net_weight:.1f}"
        except (ValueError, TypeError) as e:
            return jsonify({
                'success': False,
                'error': 'INVALID_WEIGHT_FORMAT',
                'message': '무게 형식이 올바르지 않습니다.'
            }), 400
        
        # 프린터 이름이 있으면 사용
        printer_name = data.get('printer')
        
        # PDF 생성
        pdf_path = printer.create_label_pdf(data)
        
        # 인쇄 실행
        success = printer.print_label(pdf_path, printer_name=printer_name)
        
        if success:
            return jsonify({
                'success': True, 
                'message': '라벨이 성공적으로 인쇄되었습니다.',
                'data': {
                    'net_weight': data['net_weight'],
                    'total_weight': data['total_weight'],
                    'pallet_weight': data['pallet_weight'],
                    'extra_weight': data.get('extra_weight', '0'),
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
        logger.error(f"라벨 인쇄 중 오류: {str(e)}")
        return jsonify({
            'success': False, 
            'error': 'INTERNAL_ERROR',
            'message': f'서버 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/print/bulk-sheet', methods=['POST'])
def print_bulk_sheet():
    """벌크 생산 시트 인쇄"""
    try:
        data = request.get_json() or {}
        
        if not data.get('date'):
            data['date'] = datetime.now().strftime('%Y-%m-%d')
        
        pdf_path = printer.create_bulk_production_sheet_pdf(data)
        success = printer.print_label(pdf_path)
        
        if success:
            return jsonify({
                'success': True,
                'message': '벌크 생산 시트가 성공적으로 인쇄되었습니다.',
                'data': {
                    'date': data.get('date'),
                    'shift': data.get('shift'),
                    'product_name': data.get('product_name')
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'PRINT_FAILED',
                'message': '인쇄에 실패했습니다. 프린터 설정을 확인해주세요.'
            }), 500
    except Exception as e:
        logger.error(f"벌크 생산 시트 인쇄 중 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': f'서버 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/preview/bulk-sheet', methods=['POST'])
def preview_bulk_sheet():
    """벌크 생산 시트 미리보기"""
    try:
        data = request.get_json() or {}
        if not data.get('date'):
            data['date'] = datetime.now().strftime('%Y-%m-%d')
        
        pdf_path = printer.create_bulk_production_sheet_pdf(data)
        return send_file(pdf_path, as_attachment=False, download_name='bulk_sheet_preview.pdf')
    except Exception as e:
        logger.error(f"벌크 생산 시트 미리보기 생성 중 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'PREVIEW_FAILED',
            'message': f'미리보기를 생성할 수 없습니다: {str(e)}'
        }), 500

@app.route('/api/print/batch', methods=['POST'])
def print_batch_labels():
    """여러 라벨 일괄 인쇄 API"""
    try:
        data = request.get_json()
        labels = data.get('labels', [])
        
        if not labels:
            return jsonify({
                'success': False,
                'error': 'NO_LABELS',
                'message': '인쇄할 라벨이 없습니다.'
            }), 400
        
        results = []
        success_count = 0
        
        for i, label_data in enumerate(labels):
            try:
                # 필수 데이터 검증
                if not label_data.get('total_weight') or not label_data.get('pallet_weight'):
                    results.append({
                        'index': i,
                        'success': False,
                        'error': 'WEIGHT_REQUIRED',
                        'message': '총무게와 팔렛무게 정보가 필요합니다.'
                    })
                    continue
                
                # 기본값 설정
                if not label_data.get('date'):
                    label_data['date'] = datetime.now().strftime('%Y-%m-%d')
                if not label_data.get('extra_weight'):
                    label_data['extra_weight'] = '0'
                
                # 순수무게 계산
                try:
                    total_weight = float(label_data['total_weight'])
                    pallet_weight = float(label_data['pallet_weight'])
                    extra_weight = float(label_data.get('extra_weight', 0))
                    net_weight = total_weight - pallet_weight - extra_weight
                    
                    if net_weight <= 0:
                        results.append({
                            'index': i,
                            'success': False,
                            'error': 'INVALID_WEIGHT',
                            'message': '순수무게가 0 이하입니다.'
                        })
                        continue
                    
                    label_data['net_weight'] = f"{net_weight:.1f}"
                except (ValueError, TypeError):
                    results.append({
                        'index': i,
                        'success': False,
                        'error': 'INVALID_WEIGHT_FORMAT',
                        'message': '무게 형식이 올바르지 않습니다.'
                    })
                    continue
                
                # 프린터 이름이 있으면 사용
                printer_name = label_data.get('printer')
                
                # PDF 생성 및 인쇄
                pdf_path = printer.create_label_pdf(label_data)
                success = printer.print_label(pdf_path, printer_name=printer_name)
                
                results.append({
                    'index': i,
                    'success': success,
                    'net_weight': label_data['net_weight'],
                    'total_weight': label_data['total_weight'],
                    'pallet_weight': label_data['pallet_weight']
                })
                
                if success:
                    success_count += 1
                    
            except Exception as e:
                logger.error(f"라벨 {i} 인쇄 중 오류: {str(e)}")
                results.append({
                    'index': i,
                    'success': False,
                    'error': str(e)
                })
        
        return jsonify({
            'success': success_count > 0,
            'message': f'{success_count}/{len(labels)}개 라벨이 인쇄되었습니다.',
            'results': results,
            'summary': {
                'total': len(labels),
                'success': success_count,
                'failed': len(labels) - success_count
            }
        })
        
    except Exception as e:
        logger.error(f"일괄 인쇄 중 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': f'서버 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/preview', methods=['POST'])
def preview_label():
    """라벨 미리보기"""
    try:
        data = request.get_json()
        
        # 기본값 설정
        if not data.get('date'):
            data['date'] = datetime.now().strftime('%Y-%m-%d')
        if not data.get('product_name'):
            data['product_name'] = '제품'
        
        # PDF 생성
        pdf_path = printer.create_label_pdf(data)
        
        return send_file(pdf_path, as_attachment=False, download_name='label_preview.pdf')
        
    except Exception as e:
        logger.error(f"미리보기 생성 중 오류: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/printers', methods=['GET'])
def list_printers():
    """사용 가능한 프린터 목록 조회 (모바일용)"""
    try:
        if os.name == 'posix':
            import subprocess
            result = subprocess.run(['lpstat', '-p'], capture_output=True, text=True)
            if result.returncode == 0:
                printers = []
                for line in result.stdout.split('\n'):
                    if line.startswith('printer'):
                        parts = line.split()
                        if len(parts) >= 2:
                            printer_name = parts[1]
                            # 프린터 상태 확인
                            status = 'available' if 'idle' in line else 'busy'
                            printers.append({
                                'name': printer_name,
                                'status': status,
                                'description': f'프린터 {printer_name}'
                            })
                return jsonify({
                    'success': True,
                    'printers': printers
                })
            else:
                return jsonify({
                    'success': True,
                    'printers': []
                })
        else:
            # Windows의 경우 기본 프린터만 반환
            return jsonify({
                'success': True,
                'printers': [{
                    'name': 'default',
                    'status': 'available',
                    'description': '기본 프린터'
                }]
            })
    except Exception as e:
        logger.error(f"프린터 목록 조회 중 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'PRINTER_LIST_FAILED',
            'message': f'프린터 목록 조회 실패: {str(e)}'
        }), 500

@app.route('/api/status', methods=['GET'])
def server_status():
    """서버 상태 확인 (모바일용)"""
    try:
        return jsonify({
            'success': True,
            'status': 'running',
            'server_time': datetime.now().isoformat(),
            'version': '1.0.0',
            'label_size': '10cm x 5cm'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'STATUS_CHECK_FAILED',
            'message': str(e)
        }), 500

@app.route('/api/status', methods=['GET'])
def get_server_status():
    """서버 상태 확인"""
    try:
        return jsonify({
            'success': True,
            'status': 'running',
            'version': '1.0.0',
            'label_size': '10cm x 5cm',
            'server_time': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'STATUS_CHECK_FAILED',
            'message': str(e)
        }), 500

@app.route('/api/printers', methods=['GET'])
def get_printers():
    """사용 가능한 프린터 목록 조회"""
    try:
        # 실제 구현에서는 시스템의 프린터 목록을 조회
        # 여기서는 간단한 예제만 제공
        return jsonify({
            'success': True,
            'printers': [
                {'name': '기본 프린터', 'status': '사용 가능'},
                {'name': 'Canon_TS3400_series', 'status': '사용 가능'}
            ]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'PRINTER_LIST_FAILED',
            'message': str(e)
        }), 500

@app.route('/api/print/status/<label_id>', methods=['GET'])
def get_print_status(label_id):
    """특정 라벨의 인쇄 상태 조회"""
    try:
        # 실제 구현에서는 데이터베이스에서 상태를 조회
        # 여기서는 간단한 예제만 제공
        return jsonify({
            'success': True,
            'label_id': label_id,
            'status': 'printed',
            'print_time': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'STATUS_QUERY_FAILED',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    print("라벨 인쇄 서버가 시작됩니다...")
    print("웹 브라우저에서 http://localhost:8080 을 열어주세요")
    print("모바일에서도 같은 네트워크의 IP 주소로 접속 가능합니다")
    
    app.run(host='0.0.0.0', port=8080, debug=True)
