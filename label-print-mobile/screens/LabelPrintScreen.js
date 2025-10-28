import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ScrollView,
  ActivityIndicator,
  Modal,
} from "react-native";
import { Picker } from "@react-native-picker/picker";
import LabelPrintService from "../services/LabelPrintService";

const LabelPrintScreen = () => {
  const [totalWeight, setTotalWeight] = useState("");
  const [palletWeight, setPalletWeight] = useState("");
  const [netWeight, setNetWeight] = useState("0.00 kg");
  const [selectedPrinter, setSelectedPrinter] = useState("");
  const [printers, setPrinters] = useState([]);
  const [serverStatus, setServerStatus] = useState("checking");
  const [loading, setLoading] = useState(false);
  const [showIpModal, setShowIpModal] = useState(false);
  const [serverIp, setServerIp] = useState("10.0.0.208");
  const [labels, setLabels] = useState([]);
  const [showBatchMode, setShowBatchMode] = useState(false);

  // 순수무게 자동 계산
  useEffect(() => {
    const total = parseFloat(totalWeight) || 0;
    const pallet = parseFloat(palletWeight) || 0;
    const net = total - pallet;
    setNetWeight(net > 0 ? `${net.toFixed(2)} kg` : "0.00 kg");
  }, [totalWeight, palletWeight]);

  // 컴포넌트 마운트 시 초기화
  useEffect(() => {
    checkServerStatus();
    loadPrinters();
  }, []);

  // 서버 상태 확인
  const checkServerStatus = async () => {
    const result = await LabelPrintService.checkServerStatus();
    setServerStatus(result.status);
  };

  // 프린터 목록 로드
  const loadPrinters = async () => {
    console.log("🔄 프린터 목록 로딩 시작...");
    const result = await LabelPrintService.getPrinters();
    console.log("📱 프린터 목록 API 응답:", result);

    if (result.success) {
      console.log("✅ 받은 프린터 목록:", result.printers);
      console.log("📊 프린터 배열 길이:", result.printers.length);
      setPrinters(result.printers);
      if (result.printers.length > 0 && !selectedPrinter) {
        console.log("🎯 첫 번째 프린터 선택:", result.printers[0].name);
        setSelectedPrinter(result.printers[0].name);
      }
    } else {
      console.log("❌ 프린터 목록 로딩 실패:", result.message);
    }
  };

  // 서버 IP 변경
  const handleIpChange = () => {
    setShowIpModal(true);
  };

  const confirmIpChange = () => {
    if (serverIp.trim()) {
      LabelPrintService.setServerURL(serverIp.trim());
      setShowIpModal(false);
      checkServerStatus();
      loadPrinters();
    }
  };

  // 라벨 추가 (일괄 모드)
  const addLabel = () => {
    if (!totalWeight || !palletWeight || !selectedPrinter) {
      Alert.alert("오류", "모든 필수 항목을 입력해주세요.");
      return;
    }

    const total = parseFloat(totalWeight);
    const pallet = parseFloat(palletWeight);
    const net = total - pallet;

    if (net <= 0) {
      Alert.alert("오류", "팔렛무게는 총무게보다 작아야 합니다.");
      return;
    }

    const newLabel = {
      id: Date.now().toString(),
      totalWeight: totalWeight,
      palletWeight: palletWeight,
      netWeight: net.toFixed(2),
      printer: selectedPrinter,
      date: new Date().toISOString().split("T")[0],
    };

    setLabels([...labels, newLabel]);
    resetForm();
  };

  // 라벨 제거
  const removeLabel = (id) => {
    setLabels(labels.filter((label) => label.id !== id));
  };

  // 라벨 인쇄 (단일)
  const handlePrint = async () => {
    if (showBatchMode) {
      addLabel();
      return;
    }

    // 유효성 검사
    if (!totalWeight || !palletWeight || !selectedPrinter) {
      Alert.alert("오류", "모든 필수 항목을 입력해주세요.");
      return;
    }

    const total = parseFloat(totalWeight);
    const pallet = parseFloat(palletWeight);
    const net = total - pallet;

    if (net <= 0) {
      Alert.alert("오류", "팔렛무게는 총무게보다 작아야 합니다.");
      return;
    }

    setLoading(true);

    try {
      const printData = {
        totalWeight: totalWeight,
        palletWeight: palletWeight,
        printer: selectedPrinter,
      };

      console.log("🎯 인쇄 요청 - 선택된 프린터:", selectedPrinter);
      console.log("🎯 인쇄 요청 - 전체 데이터:", printData);

      const result = await LabelPrintService.printLabel(printData);

      if (result.success) {
        Alert.alert("성공", result.message);
        resetForm();
      } else {
        Alert.alert("오류", result.message);
      }
    } catch (error) {
      Alert.alert("오류", "인쇄 중 오류가 발생했습니다: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 일괄 인쇄
  const printAllLabels = async () => {
    if (labels.length === 0) {
      Alert.alert("오류", "인쇄할 라벨이 없습니다.");
      return;
    }

    setLoading(true);

    try {
      const labelsToPrint = labels.map((label) => ({
        totalWeight: label.totalWeight,
        palletWeight: label.palletWeight,
        printer: label.printer,
      }));

      const results = await LabelPrintService.printBatchLabels(labelsToPrint);

      const successCount = results.filter((r) => r.result.success).length;
      const failCount = results.length - successCount;

      if (failCount === 0) {
        Alert.alert(
          "성공",
          `모든 라벨(${successCount}개)이 성공적으로 인쇄되었습니다!`
        );
        setLabels([]);
      } else {
        Alert.alert(
          "부분 성공",
          `성공: ${successCount}개, 실패: ${failCount}개\n실패한 항목을 확인해주세요.`
        );
      }
    } catch (error) {
      Alert.alert("오류", "일괄 인쇄 중 오류가 발생했습니다: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 폼 초기화
  const resetForm = () => {
    setTotalWeight("");
    setPalletWeight("");
    setNetWeight("0.00 kg");
    setSelectedPrinter("");
  };

  // 현재 날짜
  const currentDate = new Date().toISOString().split("T")[0];

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>🏷️ 라벨 인쇄</Text>

        <View style={styles.serverInfo}>
          <Text style={styles.serverText}>
            서버: {LabelPrintService.baseURL}
          </Text>
          <TouchableOpacity style={styles.ipButton} onPress={handleIpChange}>
            <Text style={styles.ipButtonText}>IP 변경</Text>
          </TouchableOpacity>
        </View>

        <View style={[styles.status, styles[serverStatus]]}>
          <Text style={styles.statusText}>
            {serverStatus === "connected" && "✅ 서버 연결됨"}
            {serverStatus === "disconnected" && "❌ 서버 연결 실패"}
            {serverStatus === "checking" && "⏳ 서버 연결 확인 중..."}
            {serverStatus === "error" && "⚠️ 서버 오류"}
          </Text>
        </View>
      </View>

      <View style={styles.form}>
        <View style={styles.inputGroup}>
          <Text style={styles.label}>총무게 (kg) *</Text>
          <TextInput
            style={styles.input}
            value={totalWeight}
            onChangeText={setTotalWeight}
            placeholder="총무게를 입력하세요"
            keyboardType="numeric"
            returnKeyType="next"
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>팔렛무게 (kg) *</Text>
          <TextInput
            style={styles.input}
            value={palletWeight}
            onChangeText={setPalletWeight}
            placeholder="팔렛무게를 입력하세요"
            keyboardType="numeric"
            returnKeyType="next"
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>순수무게 (kg)</Text>
          <View style={styles.displayField}>
            <Text style={styles.displayText}>{netWeight}</Text>
          </View>
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>날짜</Text>
          <View style={styles.displayField}>
            <Text style={styles.displayText}>{currentDate}</Text>
          </View>
        </View>

        <View style={styles.inputGroup}>
          <View style={styles.printerHeader}>
            <Text style={styles.label}>프린터 선택 *</Text>
            <TouchableOpacity
              style={styles.refreshButton}
              onPress={loadPrinters}
            >
              <Text style={styles.refreshButtonText}>🔄 새로고침</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.pickerContainer}>
            <Picker
              selectedValue={selectedPrinter}
              onValueChange={(itemValue) => {
                if (itemValue && itemValue !== "") {
                  console.log("🎯 프린터 선택 변경:", itemValue);
                  setSelectedPrinter(itemValue);
                }
              }}
              style={styles.picker}
              itemStyle={styles.pickerItem}
            >
              {printers.length === 0 ? (
                <Picker.Item label="프린터를 불러오는 중..." value="" />
              ) : (
                printers.map((printer, index) => (
                  <Picker.Item
                    key={index}
                    label={`${printer.name} (${printer.status})`}
                    value={printer.name}
                  />
                ))
              )}
            </Picker>
          </View>
        </View>

        <TouchableOpacity
          style={[styles.modeButton, showBatchMode && styles.modeButtonActive]}
          onPress={() => setShowBatchMode(!showBatchMode)}
        >
          <Text
            style={[
              styles.modeButtonText,
              showBatchMode && styles.modeButtonTextActive,
            ]}
          >
            {showBatchMode ? "📋 일괄 모드" : "📄 단일 모드"}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[
            styles.printButton,
            (loading || !selectedPrinter) && styles.buttonDisabled,
          ]}
          onPress={handlePrint}
          disabled={loading || !selectedPrinter}
        >
          {loading ? (
            <ActivityIndicator color="white" />
          ) : (
            <Text style={styles.printButtonText}>
              {showBatchMode ? "➕ 라벨 추가" : "🖨️ 라벨 인쇄"}
            </Text>
          )}
        </TouchableOpacity>

        {showBatchMode && labels.length > 0 && (
          <TouchableOpacity
            style={[styles.printAllButton, loading && styles.buttonDisabled]}
            onPress={printAllLabels}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="white" />
            ) : (
              <Text style={styles.printAllButtonText}>
                🖨️ 전체 인쇄 ({labels.length}개)
              </Text>
            )}
          </TouchableOpacity>
        )}

        <TouchableOpacity style={styles.resetButton} onPress={resetForm}>
          <Text style={styles.resetButtonText}>🔄 초기화</Text>
        </TouchableOpacity>
      </View>

      {/* 라벨 목록 (일괄 모드일 때만 표시) */}
      {showBatchMode && (
        <View style={styles.labelsSection}>
          <Text style={styles.sectionTitle}>라벨 목록 ({labels.length}개)</Text>

          {labels.length === 0 ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyText}>추가된 라벨이 없습니다.</Text>
              <Text style={styles.emptySubText}>
                위의 폼을 사용하여 라벨을 추가하세요.
              </Text>
            </View>
          ) : (
            <View style={styles.labelsList}>
              {labels.map((label) => (
                <View key={label.id} style={styles.labelItem}>
                  <View style={styles.labelInfo}>
                    <Text style={styles.labelText}>
                      총: {label.totalWeight}kg | 팔렛: {label.palletWeight}kg |
                      순수: {label.netWeight}kg
                    </Text>
                    <Text style={styles.labelDate}>{label.date}</Text>
                  </View>
                  <TouchableOpacity
                    style={styles.removeButton}
                    onPress={() => removeLabel(label.id)}
                  >
                    <Text style={styles.removeButtonText}>삭제</Text>
                  </TouchableOpacity>
                </View>
              ))}
            </View>
          )}
        </View>
      )}

      {/* IP 변경 모달 */}
      <Modal
        visible={showIpModal}
        transparent={true}
        animationType="slide"
        onRequestClose={() => setShowIpModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>서버 IP 주소 설정</Text>
            <TextInput
              style={styles.modalInput}
              value={serverIp}
              onChangeText={setServerIp}
              placeholder="IP 주소를 입력하세요 (예: 192.168.1.100)"
              keyboardType="numeric"
            />
            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={[styles.modalButton, styles.cancelButton]}
                onPress={() => setShowIpModal(false)}
              >
                <Text style={styles.cancelButtonText}>취소</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.confirmButton]}
                onPress={confirmIpChange}
              >
                <Text style={styles.confirmButtonText}>확인</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f5f5f5",
  },
  header: {
    padding: 20,
    backgroundColor: "white",
    marginBottom: 10,
  },
  title: {
    fontSize: 24,
    fontWeight: "bold",
    textAlign: "center",
    marginBottom: 20,
    color: "#333",
  },
  serverInfo: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: "#f8f9fa",
    padding: 10,
    borderRadius: 5,
    marginBottom: 10,
  },
  serverText: {
    fontSize: 14,
    color: "#666",
  },
  ipButton: {
    backgroundColor: "#4CAF50",
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 3,
  },
  ipButtonText: {
    color: "white",
    fontSize: 12,
    fontWeight: "600",
  },
  status: {
    padding: 10,
    borderRadius: 8,
    alignItems: "center",
  },
  connected: {
    backgroundColor: "#d4edda",
    borderColor: "#c3e6cb",
    borderWidth: 1,
  },
  disconnected: {
    backgroundColor: "#f8d7da",
    borderColor: "#f5c6cb",
    borderWidth: 1,
  },
  checking: {
    backgroundColor: "#fff3cd",
    borderColor: "#ffeaa7",
    borderWidth: 1,
  },
  error: {
    backgroundColor: "#f8d7da",
    borderColor: "#f5c6cb",
    borderWidth: 1,
  },
  statusText: {
    fontSize: 14,
    fontWeight: "600",
  },
  form: {
    padding: 20,
  },
  inputGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    fontWeight: "600",
    marginBottom: 8,
    color: "#555",
  },
  input: {
    backgroundColor: "white",
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
  },
  displayField: {
    backgroundColor: "#f8f9fa",
    borderWidth: 1,
    borderColor: "#e9ecef",
    borderRadius: 8,
    padding: 12,
  },
  displayText: {
    fontSize: 16,
    color: "#666",
  },
  printerContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
  },
  printerOption: {
    backgroundColor: "white",
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 8,
    padding: 10,
    minWidth: 120,
    marginRight: 10,
    marginBottom: 10,
  },
  printerSelected: {
    backgroundColor: "#e3f2fd",
    borderColor: "#2196F3",
  },
  printerText: {
    fontSize: 14,
    textAlign: "center",
  },
  printerTextSelected: {
    color: "#1976d2",
    fontWeight: "600",
  },
  printButton: {
    backgroundColor: "#4CAF50",
    padding: 15,
    borderRadius: 8,
    alignItems: "center",
    marginBottom: 10,
  },
  printButtonText: {
    color: "white",
    fontSize: 16,
    fontWeight: "600",
  },
  resetButton: {
    backgroundColor: "#f44336",
    padding: 15,
    borderRadius: 8,
    alignItems: "center",
  },
  resetButtonText: {
    color: "white",
    fontSize: 16,
    fontWeight: "600",
  },
  buttonDisabled: {
    backgroundColor: "#cccccc",
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.5)",
    justifyContent: "center",
    alignItems: "center",
  },
  modalContent: {
    backgroundColor: "white",
    padding: 20,
    borderRadius: 10,
    width: "80%",
    maxWidth: 400,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: "bold",
    marginBottom: 15,
    textAlign: "center",
  },
  modalInput: {
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 20,
  },
  modalButtons: {
    flexDirection: "row",
    justifyContent: "space-between",
  },
  modalButton: {
    flex: 1,
    padding: 12,
    borderRadius: 8,
    alignItems: "center",
    marginHorizontal: 5,
  },
  cancelButton: {
    backgroundColor: "#f44336",
  },
  confirmButton: {
    backgroundColor: "#4CAF50",
  },
  cancelButtonText: {
    color: "white",
    fontWeight: "600",
  },
  confirmButtonText: {
    color: "white",
    fontWeight: "600",
  },
  modeButton: {
    backgroundColor: "#2196F3",
    padding: 15,
    borderRadius: 8,
    alignItems: "center",
    marginBottom: 10,
  },
  modeButtonActive: {
    backgroundColor: "#4CAF50",
  },
  modeButtonText: {
    color: "white",
    fontSize: 16,
    fontWeight: "600",
  },
  modeButtonTextActive: {
    color: "white",
  },
  printAllButton: {
    backgroundColor: "#FF9800",
    padding: 15,
    borderRadius: 8,
    alignItems: "center",
    marginBottom: 10,
  },
  printAllButtonText: {
    color: "white",
    fontSize: 16,
    fontWeight: "600",
  },
  labelsSection: {
    padding: 20,
    backgroundColor: "white",
    marginTop: 10,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "bold",
    marginBottom: 15,
    color: "#333",
  },
  labelsList: {
    maxHeight: 300,
  },
  labelItem: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: "#f8f9fa",
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: "#e9ecef",
  },
  labelInfo: {
    flex: 1,
  },
  labelText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#333",
  },
  labelDate: {
    fontSize: 12,
    color: "#666",
    marginTop: 4,
  },
  removeButton: {
    backgroundColor: "#f44336",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  removeButtonText: {
    color: "white",
    fontSize: 12,
    fontWeight: "600",
  },
  pickerContainer: {
    backgroundColor: "white",
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 8,
    marginTop: 8,
  },
  picker: {
    height: 50,
  },
  pickerItem: {
    fontSize: 16,
  },
  printerHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  refreshButton: {
    backgroundColor: "#2196F3",
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 5,
  },
  refreshButtonText: {
    color: "white",
    fontSize: 12,
    fontWeight: "600",
  },
  emptyState: {
    alignItems: "center",
    padding: 40,
  },
  emptyText: {
    fontSize: 16,
    color: "#666",
    marginBottom: 8,
  },
  emptySubText: {
    fontSize: 14,
    color: "#999",
  },
});

export default LabelPrintScreen;
