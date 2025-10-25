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
        if 'product_name' in data:
            c.setFont("Helvetica-Bold", 14)
            c.drawString(0.5*cm, LABEL_HEIGHT-1.5*cm, data['product_name'][:20])
        
        # 무게 정보 (중앙, 큰 글씨)
        if 'weight' in data:
            c.setFont("Helvetica-Bold", 24)
            weight_text = f"{data['weight']} kg"
            text_width = c.stringWidth(weight_text, "Helvetica-Bold", 24)
            x_pos = (LABEL_WIDTH - text_width) / 2
            c.drawString(x_pos, LABEL_HEIGHT/2 - 0.5*cm, weight_text)
        
        # 날짜 (하단)
        if 'date' in data:
            c.setFont("Helvetica", 10)
            c.drawString(0.5*cm, 0.8*cm, f"날짜: {data['date']}")
        
        # 바코드 영역 (우측 하단)
        if 'barcode' in data:
            c.setFont("Helvetica", 8)
            c.drawString(LABEL_WIDTH-3*cm, 0.5*cm, f"ID: {data['barcode']}")
        
        # 추가 정보
        if 'additional_info' in data:
            c.setFont("Helvetica", 9)
            c.drawString(0.5*cm, 1.5*cm, data['additional_info'][:30])
        
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
            .container { max-width: 600px; margin: 0 auto; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            button { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background-color: #0056b3; }
            .preview { border: 1px solid #ccc; padding: 20px; margin: 20px 0; background: white; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>라벨 인쇄 서버</h1>
            <p>10cm x 5cm 크기의 라벨을 인쇄할 수 있습니다.</p>
            
            <form id="labelForm">
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
                
                <div class="form-group">
                    <label for="additional_info">추가 정보:</label>
                    <textarea id="additional_info" name="additional_info" rows="2" placeholder="추가 정보를 입력하세요"></textarea>
                </div>
                
                <button type="submit">라벨 인쇄</button>
            </form>
            
            <div id="result"></div>
        </div>
        
        <script>
            document.getElementById('date').value = new Date().toISOString().split('T')[0];
            
            document.getElementById('labelForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const formData = new FormData(this);
                const data = Object.fromEntries(formData);
                
                try {
                    const response = await fetch('/print', {
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
        </script>
    </body>
    </html>
    """

@app.route('/api/print', methods=['POST'])
def print_label():
    """라벨 인쇄 API (모바일용)"""
    try:
        data = request.get_json()
        
        # 필수 데이터 검증
        if not data.get('weight'):
            return jsonify({
                'success': False, 
                'error': 'WEIGHT_REQUIRED',
                'message': '무게 정보가 필요합니다.'
            }), 400
        
        # 기본값 설정
        if not data.get('date'):
            data['date'] = datetime.now().strftime('%Y-%m-%d')
        
        if not data.get('product_name'):
            data['product_name'] = '제품'
        
        if not data.get('barcode'):
            data['barcode'] = f"ID{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # PDF 생성
        pdf_path = printer.create_label_pdf(data)
        
        # 인쇄 실행
        success = printer.print_label(pdf_path)
        
        if success:
            return jsonify({
                'success': True, 
                'message': '라벨이 성공적으로 인쇄되었습니다.',
                'data': {
                    'label_id': data.get('barcode'),
                    'weight': data.get('weight'),
                    'product_name': data.get('product_name'),
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
                # 기본값 설정
                if not label_data.get('date'):
                    label_data['date'] = datetime.now().strftime('%Y-%m-%d')
                if not label_data.get('product_name'):
                    label_data['product_name'] = f'제품 {i+1}'
                if not label_data.get('barcode'):
                    label_data['barcode'] = f"ID{datetime.now().strftime('%Y%m%d%H%M%S')}{i}"
                
                # PDF 생성 및 인쇄
                pdf_path = printer.create_label_pdf(label_data)
                success = printer.print_label(pdf_path)
                
                results.append({
                    'index': i,
                    'success': success,
                    'label_id': label_data.get('barcode'),
                    'weight': label_data.get('weight')
                })
                
                if success:
                    success_count += 1
                    
            except Exception as e:
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
    print("웹 브라우저에서 http://localhost:5000 을 열어주세요")
    print("모바일에서도 같은 네트워크의 IP 주소로 접속 가능합니다")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
