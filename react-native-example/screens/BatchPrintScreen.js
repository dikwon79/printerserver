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
} from "react-native";
import { Ionicons } from "@expo/vector-icons";

const SERVER_URL = "http://10.0.0.208:8080";

export default function BatchPrintScreen() {
  const [labels, setLabels] = useState([]);
  const [currentLabel, setCurrentLabel] = useState({
    totalWeight: "",
    palletWeight: "",
    netWeight: 0,
  });
  const [printer, setPrinter] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [availablePrinters, setAvailablePrinters] = useState(["기본 프린터"]);

  // 순수무게 자동 계산
  useEffect(() => {
    const total = parseFloat(currentLabel.totalWeight) || 0;
    const pallet = parseFloat(currentLabel.palletWeight) || 0;
    const net = total - pallet;
    setCurrentLabel((prev) => ({ ...prev, netWeight: net > 0 ? net : 0 }));
  }, [currentLabel.totalWeight, currentLabel.palletWeight]);

  // 서버 상태 확인
  useEffect(() => {
    checkServerStatus();
    const interval = setInterval(checkServerStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const checkServerStatus = async () => {
    try {
      const response = await fetch(`${SERVER_URL}/api/status`);
      if (response.ok) {
        setIsConnected(true);
      } else {
        setIsConnected(false);
      }
    } catch (error) {
      setIsConnected(false);
    }
  };

  const addLabel = () => {
    if (!currentLabel.totalWeight || !currentLabel.palletWeight) {
      Alert.alert("오류", "총무게와 팔렛무게를 모두 입력해주세요.");
      return;
    }

    if (currentLabel.netWeight <= 0) {
      Alert.alert("오류", "팔렛무게는 총무게보다 작아야 합니다.");
      return;
    }

    const newLabel = {
      id: Date.now().toString(),
      ...currentLabel,
    };

    setLabels((prev) => [...prev, newLabel]);
    setCurrentLabel({
      totalWeight: "",
      palletWeight: "",
      netWeight: 0,
    });
  };

  const removeLabel = (id) => {
    setLabels((prev) => prev.filter((label) => label.id !== id));
  };

  const printAllLabels = async () => {
    if (labels.length === 0) {
      Alert.alert("오류", "인쇄할 라벨이 없습니다.");
      return;
    }

    if (!printer) {
      Alert.alert("오류", "프린터를 선택해주세요.");
      return;
    }

    setIsLoading(true);

    try {
      for (const label of labels) {
        const response = await fetch(`${SERVER_URL}/api/print`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            total_weight: label.totalWeight,
            pallet_weight: label.palletWeight,
            printer: printer,
          }),
        });

        const result = await response.json();

        if (!result.success) {
          Alert.alert("오류", `라벨 인쇄 실패: ${result.message}`);
          return;
        }
      }

      Alert.alert(
        "성공",
        `${labels.length}개의 라벨이 성공적으로 인쇄되었습니다!`
      );
      setLabels([]);
    } catch (error) {
      Alert.alert("오류", "서버 연결에 실패했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  const clearAllLabels = () => {
    Alert.alert("확인", "모든 라벨을 삭제하시겠습니까?", [
      { text: "취소", style: "cancel" },
      { text: "삭제", style: "destructive", onPress: () => setLabels([]) },
    ]);
  };

  const renderLabelItem = ({ item }) => (
    <View style={styles.labelItem}>
      <View style={styles.labelInfo}>
        <Text style={styles.labelText}>총무게: {item.totalWeight}kg</Text>
        <Text style={styles.labelText}>팔렛무게: {item.palletWeight}kg</Text>
        <Text style={styles.labelText}>
          순수무게: {item.netWeight.toFixed(2)}kg
        </Text>
      </View>
      <TouchableOpacity
        style={styles.removeButton}
        onPress={() => removeLabel(item.id)}
      >
        <Ionicons name="close" size={20} color="#f44336" />
      </TouchableOpacity>
    </View>
  );

  return (
    <ScrollView style={styles.container}>
      <View style={styles.statusContainer}>
        <View
          style={[
            styles.statusIndicator,
            { backgroundColor: isConnected ? "#4CAF50" : "#f44336" },
          ]}
        />
        <Text style={styles.statusText}>
          {isConnected ? "✅ 서버 연결됨" : "❌ 서버 연결 실패"}
        </Text>
      </View>

      <View style={styles.formContainer}>
        <Text style={styles.sectionTitle}>새 라벨 추가</Text>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>총무게 (kg) *</Text>
          <TextInput
            style={styles.input}
            value={currentLabel.totalWeight}
            onChangeText={(text) =>
              setCurrentLabel((prev) => ({ ...prev, totalWeight: text }))
            }
            placeholder="총무게를 입력하세요"
            keyboardType="numeric"
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>팔렛무게 (kg) *</Text>
          <TextInput
            style={styles.input}
            value={currentLabel.palletWeight}
            onChangeText={(text) =>
              setCurrentLabel((prev) => ({ ...prev, palletWeight: text }))
            }
            placeholder="팔렛무게를 입력하세요"
            keyboardType="numeric"
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>순수무게 (kg)</Text>
          <View style={styles.displayField}>
            <Text style={styles.displayText}>
              {currentLabel.netWeight.toFixed(2)} kg
            </Text>
          </View>
        </View>

        <TouchableOpacity style={styles.addButton} onPress={addLabel}>
          <Ionicons name="add" size={20} color="#fff" />
          <Text style={styles.addButtonText}>라벨 추가</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.labelsContainer}>
        <View style={styles.labelsHeader}>
          <Text style={styles.sectionTitle}>인쇄 목록 ({labels.length}개)</Text>
          {labels.length > 0 && (
            <TouchableOpacity
              style={styles.clearButton}
              onPress={clearAllLabels}
            >
              <Text style={styles.clearButtonText}>전체 삭제</Text>
            </TouchableOpacity>
          )}
        </View>

        {labels.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>추가된 라벨이 없습니다.</Text>
          </View>
        ) : (
          <FlatList
            data={labels}
            renderItem={renderLabelItem}
            keyExtractor={(item) => item.id}
            scrollEnabled={false}
          />
        )}
      </View>

      {labels.length > 0 && (
        <View style={styles.printContainer}>
          <View style={styles.inputGroup}>
            <Text style={styles.label}>프린터 선택 *</Text>
            <View style={styles.printerContainer}>
              {availablePrinters.map((printerName, index) => (
                <TouchableOpacity
                  key={index}
                  style={[
                    styles.printerButton,
                    printer === printerName && styles.printerButtonSelected,
                  ]}
                  onPress={() => setPrinter(printerName)}
                >
                  <Text
                    style={[
                      styles.printerButtonText,
                      printer === printerName &&
                        styles.printerButtonTextSelected,
                    ]}
                  >
                    {printerName}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          <TouchableOpacity
            style={[
              styles.printButton,
              isLoading && styles.printButtonDisabled,
            ]}
            onPress={printAllLabels}
            disabled={isLoading}
          >
            {isLoading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <>
                <Ionicons name="print" size={20} color="#fff" />
                <Text style={styles.printButtonText}>
                  전체 인쇄 ({labels.length}개)
                </Text>
              </>
            )}
          </TouchableOpacity>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f5f5f5",
  },
  statusContainer: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    padding: 15,
    backgroundColor: "#fff",
    marginBottom: 10,
  },
  statusIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 8,
  },
  statusText: {
    fontSize: 16,
    fontWeight: "600",
  },
  formContainer: {
    backgroundColor: "#fff",
    margin: 15,
    padding: 20,
    borderRadius: 10,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  labelsContainer: {
    backgroundColor: "#fff",
    margin: 15,
    padding: 20,
    borderRadius: 10,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  printContainer: {
    backgroundColor: "#fff",
    margin: 15,
    padding: 20,
    borderRadius: 10,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "bold",
    marginBottom: 15,
    color: "#333",
  },
  labelsHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 15,
  },
  clearButton: {
    backgroundColor: "#f44336",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  clearButtonText: {
    color: "#fff",
    fontSize: 12,
    fontWeight: "600",
  },
  inputGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    fontWeight: "600",
    marginBottom: 8,
    color: "#333",
  },
  input: {
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: "#fff",
  },
  displayField: {
    backgroundColor: "#e3f2fd",
    borderWidth: 1,
    borderColor: "#bbdefb",
    borderRadius: 8,
    padding: 12,
  },
  displayText: {
    fontSize: 16,
    fontWeight: "bold",
    color: "#1976d2",
  },
  addButton: {
    backgroundColor: "#2196F3",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    padding: 15,
    borderRadius: 8,
  },
  addButtonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
    marginLeft: 8,
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
    color: "#333",
    marginBottom: 2,
  },
  removeButton: {
    padding: 8,
  },
  emptyContainer: {
    padding: 40,
    alignItems: "center",
  },
  emptyText: {
    fontSize: 16,
    color: "#666",
  },
  printerContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
  },
  printerButton: {
    backgroundColor: "#f5f5f5",
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 8,
    padding: 12,
    marginRight: 10,
    marginBottom: 10,
  },
  printerButtonSelected: {
    backgroundColor: "#4CAF50",
    borderColor: "#4CAF50",
  },
  printerButtonText: {
    fontSize: 14,
    color: "#333",
  },
  printerButtonTextSelected: {
    color: "#fff",
    fontWeight: "600",
  },
  printButton: {
    backgroundColor: "#4CAF50",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    padding: 15,
    borderRadius: 8,
  },
  printButtonDisabled: {
    backgroundColor: "#cccccc",
  },
  printButtonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
    marginLeft: 8,
  },
});
