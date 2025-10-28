class LabelPrintService {
  constructor() {
    // 기본 서버 URL - IP 변경 기능으로 동적 설정 가능
    this.baseURL = "http://10.0.0.208:8080";
  }

  // 서버 URL 설정
  setServerURL(ip) {
    this.baseURL = `http://${ip}:8080`;
  }

  // 서버 상태 확인
  async checkServerStatus() {
    try {
      const response = await fetch(`${this.baseURL}/api/status`, {
        method: "GET",
        timeout: 5000,
      });

      if (response.ok) {
        const data = await response.json();
        return {
          success: true,
          status: "connected",
          data: data,
        };
      } else {
        return {
          success: false,
          status: "error",
          message: "서버 응답 오류",
        };
      }
    } catch (error) {
      return {
        success: false,
        status: "disconnected",
        message: "서버 연결 실패: " + error.message,
      };
    }
  }

  // 프린터 목록 가져오기
  async getPrinters() {
    try {
      console.log(
        "🔍 프린터 목록 API 호출 시작:",
        `${this.baseURL}/api/printers`
      );

      const response = await fetch(`${this.baseURL}/api/printers`, {
        method: "GET",
        timeout: 5000,
      });

      console.log("📡 API 응답 상태:", response.status, response.ok);

      if (response.ok) {
        const data = await response.json();
        console.log("📋 API 응답 데이터:", JSON.stringify(data, null, 2));
        console.log(
          "🖨️ 프린터 개수:",
          data.printers ? data.printers.length : 0
        );

        return {
          success: true,
          printers: data.printers || [],
        };
      } else {
        console.log("❌ API 응답 실패:", response.status);
        return {
          success: false,
          printers: [],
          message: "프린터 목록을 가져올 수 없습니다",
        };
      }
    } catch (error) {
      console.log("💥 API 호출 오류:", error);
      return {
        success: false,
        printers: [],
        message: "프린터 목록 조회 실패: " + error.message,
      };
    }
  }

  // 라벨 인쇄
  async printLabel(labelData) {
    try {
      console.log("🖨️ 인쇄 요청 데이터:", labelData);

      const requestData = {
        total_weight: labelData.totalWeight,
        pallet_weight: labelData.palletWeight,
        printer: labelData.printer,
      };

      console.log("📤 API로 전송할 데이터:", requestData);

      const response = await fetch(`${this.baseURL}/api/print`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestData),
        timeout: 10000,
      });

      console.log("📡 인쇄 API 응답 상태:", response.status);

      const result = await response.json();
      console.log("📋 인쇄 API 응답 데이터:", result);

      if (result.success) {
        return {
          success: true,
          message: "라벨이 성공적으로 인쇄되었습니다!",
          data: result.data,
        };
      } else {
        return {
          success: false,
          message: result.message || "인쇄에 실패했습니다",
        };
      }
    } catch (error) {
      console.log("💥 인쇄 API 호출 오류:", error);
      return {
        success: false,
        message: "서버 연결 오류: " + error.message,
      };
    }
  }

  // 일괄 라벨 인쇄
  async printBatchLabels(labels) {
    const results = [];

    for (let i = 0; i < labels.length; i++) {
      const label = labels[i];
      const result = await this.printLabel(label);
      results.push({
        index: i + 1,
        label: label,
        result: result,
      });

      // 각 인쇄 사이에 1초 대기 (프린터 부하 방지)
      if (i < labels.length - 1) {
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }
    }

    return results;
  }
}

export default new LabelPrintService();
