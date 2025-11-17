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
  FlatList,
  Modal,
} from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import LabelPrintService from "../services/LabelPrintService";

const BatchPrintScreen = () => {
  const [totalWeight, setTotalWeight] = useState("");
  const [palletWeight, setPalletWeight] = useState("");
  const [extraWeight, setExtraWeight] = useState("");
  const [netWeight, setNetWeight] = useState("0.00 kg");
  const [selectedPrinter, setSelectedPrinter] = useState("");
  const [printers, setPrinters] = useState([]);
  const [labels, setLabels] = useState([]);
  const [serverStatus, setServerStatus] = useState("checking");
  const [loading, setLoading] = useState(false);
  const [showIpModal, setShowIpModal] = useState(false);
  const [serverIp, setServerIp] = useState("10.0.0.208");

  // 저장된 설정 불러오기
  useEffect(() => {
    loadSavedSettings();
  }, []);

  // 저장된 설정 불러오기
  const loadSavedSettings = async () => {
    try {
      const savedIp = await AsyncStorage.getItem("serverIp");
      const savedPrinter = await AsyncStorage.getItem("selectedPrinter");
      const savedExtraWeight = await AsyncStorage.getItem("extraWeight");

      if (savedIp) {
        setServerIp(savedIp);
        LabelPrintService.setServerURL(savedIp);
      }

      if (savedPrinter) {
        setSelectedPrinter(savedPrinter);
      }

      if (savedExtraWeight) {
        setExtraWeight(savedExtraWeight);
      }
    } catch (error) {
      console.log("설정 불러오기 오류:", error);
    }
  };

  // 순수무게 자동 계산
  useEffect(() => {
    const total = parseFloat(totalWeight) || 0;
    const pallet = parseFloat(palletWeight) || 0;
    const extra = parseFloat(extraWeight) || 0;
    const net = total - pallet - extra;
    setNetWeight(net > 0 ? `${net.toFixed(2)} kg` : "0.00 kg");
  }, [totalWeight, palletWeight, extraWeight]);

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
    const result = await LabelPrintService.getPrinters();
    if (result.success) {
      setPrinters(result.printers);
      
      // 저장된 프린터가 있으면 사용, 없으면 첫 번째 프린터 선택
      const savedPrinter = await AsyncStorage.getItem("selectedPrinter");
      if (savedPrinter && result.printers.some(p => p.name === savedPrinter)) {
        setSelectedPrinter(savedPrinter);
      } else if (result.printers.length > 0 && !selectedPrinter) {
        const firstPrinter = result.printers[0].name;
        setSelectedPrinter(firstPrinter);
        await AsyncStorage.setItem("selectedPrinter", firstPrinter);
      }
    }
  };

  // 서버 IP 변경
  const handleIpChange = () => {
    setShowIpModal(true);
  };

  const confirmIpChange = async () => {
    if (serverIp.trim()) {
      const ip = serverIp.trim();
      LabelPrintService.setServerURL(ip);
      await AsyncStorage.setItem("serverIp", ip);
      setShowIpModal(false);
      checkServerStatus();
      loadPrinters();
    }
  };

  // 라벨 추가
  const addLabel = () => {
    if (!totalWeight || !palletWeight || !selectedPrinter) {
      Alert.alert("오류", "모든 필수 항목을 입력해주세요.");
      return;
    }

    const total = parseFloat(totalWeight);
    const pallet = parseFloat(palletWeight);
    const extra = parseFloat(extraWeight) || 0;
    const net = total - pallet - extra;

    if (net <= 0) {
      Alert.alert("오류", "순수무게가 0 이하입니다. 무게를 확인해주세요.");
      return;
    }

    const newLabel = {
      id: Date.now().toString(),
      totalWeight: totalWeight,
      palletWeight: palletWeight,
      extraWeight: extraWeight || "0",
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

  // 폼 초기화
  const resetForm = async () => {
    setTotalWeight("");
    setPalletWeight("");
    setNetWeight("0.00 kg");
    // 저장된 기타 무게는 항상 유지 (초기화하지 않음)
    const savedExtraWeight = await AsyncStorage.getItem("extraWeight");
    if (savedExtraWeight) {
      setExtraWeight(savedExtraWeight);
    }
    // extraWeight는 초기화하지 않고 현재 값 유지
  };

  // 전체 인쇄
  const printAllLabels = async () => {
    if (labels.length === 0) {
      Alert.alert("오류", "인쇄할 라벨이 없습니다.");
      return;
    }

    if (!selectedPrinter) {
      Alert.alert("오류", "프린터를 선택해주세요.");
      return;
    }

    setLoading(true);

    try {
      // 모든 라벨에 선택된 프린터 적용
      const labelsToPrint = labels.map((label) => ({
        totalWeight: label.totalWeight,
        palletWeight: label.palletWeight,
        extraWeight: label.extraWeight || "0",
        printer: selectedPrinter,
      }));

      const results = await LabelPrintService.printBatchLabels(labelsToPrint);

      // 결과 분석
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

  // 라벨 아이템 렌더링
  const renderLabelItem = ({ item }) => (
    <View style={styles.labelItem}>
      <View style={styles.labelInfo}>
        <Text style={styles.labelText}>
          총: {item.totalWeight}kg | 팔렛: {item.palletWeight}kg | 순수:{" "}
          {item.netWeight}kg
        </Text>
        <Text style={styles.labelDate}>{item.date}</Text>
      </View>
      <TouchableOpacity
        style={styles.removeButton}
        onPress={() => removeLabel(item.id)}
      >
        <Text style={styles.removeButtonText}>삭제</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>🏷️ 라벨 일괄 인쇄</Text>

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
        <Text style={styles.sectionTitle}>라벨 추가</Text>

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
          <Text style={styles.label}>기타 무게 (kg)</Text>
          <TextInput
            style={styles.input}
            value={extraWeight}
            onChangeText={async (text) => {
              setExtraWeight(text);
              // 기타 무게 저장
              await AsyncStorage.setItem("extraWeight", text);
            }}
            placeholder="기타 무게를 입력하세요 (선택사항)"
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

        <TouchableOpacity style={styles.addButton} onPress={addLabel}>
          <Text style={styles.addButtonText}>➕ 라벨 추가</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.labelsSection}>
        <View style={styles.labelsHeader}>
          <Text style={styles.sectionTitle}>라벨 목록 ({labels.length}개)</Text>
          {labels.length > 0 && (
            <View style={styles.printerSelector}>
              <Text style={styles.label}>프린터 선택:</Text>
              <View style={styles.printerContainer}>
                {printers.map((printer, index) => (
                  <TouchableOpacity
                    key={index}
                    style={[
                      styles.printerOption,
                      selectedPrinter === printer.name &&
                        styles.printerSelected,
                    ]}
                    onPress={async () => {
                      setSelectedPrinter(printer.name);
                      // 선택한 프린터 저장
                      await AsyncStorage.setItem("selectedPrinter", printer.name);
                    }}
                  >
                    <Text
                      style={[
                        styles.printerText,
                        selectedPrinter === printer.name &&
                          styles.printerTextSelected,
                      ]}
                    >
                      {printer.name}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          )}
        </View>

        {labels.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>추가된 라벨이 없습니다.</Text>
            <Text style={styles.emptySubText}>
              위의 폼을 사용하여 라벨을 추가하세요.
            </Text>
          </View>
        ) : (
          <FlatList
            data={labels}
            renderItem={renderLabelItem}
            keyExtractor={(item) => item.id}
            style={styles.labelsList}
            showsVerticalScrollIndicator={false}
          />
        )}

        {labels.length > 0 && (
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
      </View>

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
    backgroundColor: "white",
    marginBottom: 10,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "bold",
    marginBottom: 15,
    color: "#333",
  },
  inputGroup: {
    marginBottom: 15,
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
  addButton: {
    backgroundColor: "#2196F3",
    padding: 15,
    borderRadius: 8,
    alignItems: "center",
    marginTop: 10,
  },
  addButtonText: {
    color: "white",
    fontSize: 16,
    fontWeight: "600",
  },
  labelsSection: {
    padding: 20,
    backgroundColor: "white",
  },
  labelsHeader: {
    marginBottom: 15,
  },
  printerSelector: {
    marginTop: 10,
  },
  printerContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    marginTop: 8,
  },
  printerOption: {
    backgroundColor: "white",
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 8,
    padding: 8,
    minWidth: 100,
    marginRight: 10,
    marginBottom: 10,
  },
  printerSelected: {
    backgroundColor: "#e3f2fd",
    borderColor: "#2196F3",
  },
  printerText: {
    fontSize: 12,
    textAlign: "center",
  },
  printerTextSelected: {
    color: "#1976d2",
    fontWeight: "600",
  },
  labelsList: {
    maxHeight: 300,
    marginBottom: 15,
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
  printAllButton: {
    backgroundColor: "#4CAF50",
    padding: 15,
    borderRadius: 8,
    alignItems: "center",
  },
  printAllButtonText: {
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
});

export default BatchPrintScreen;
