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
} from "react-native";
import { Ionicons } from "@expo/vector-icons";

const SERVER_URL = "http://10.0.0.208:8080";

export default function LabelPrintScreen() {
  const [totalWeight, setTotalWeight] = useState("");
  const [palletWeight, setPalletWeight] = useState("");
  const [netWeight, setNetWeight] = useState(0);
  const [printer, setPrinter] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [availablePrinters, setAvailablePrinters] = useState(["기본 프린터"]);

  // 순수무게 자동 계산
  useEffect(() => {
    const total = parseFloat(totalWeight) || 0;
    const pallet = parseFloat(palletWeight) || 0;
    const net = total - pallet;
    setNetWeight(net > 0 ? net : 0);
  }, [totalWeight, palletWeight]);

  // 서버 상태 확인
  useEffect(() => {
    checkServerStatus();
    const interval = setInterval(checkServerStatus, 30000); // 30초마다 확인
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

  const handlePrint = async () => {
    if (!totalWeight || !palletWeight || !printer) {
      Alert.alert("오류", "모든 필수 항목을 입력해주세요.");
      return;
    }

    if (netWeight <= 0) {
      Alert.alert("오류", "팔렛무게는 총무게보다 작아야 합니다.");
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch(`${SERVER_URL}/api/print`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          total_weight: totalWeight,
          pallet_weight: palletWeight,
          printer: printer,
        }),
      });

      const result = await response.json();

      if (result.success) {
        Alert.alert("성공", "라벨이 성공적으로 인쇄되었습니다!");
        resetForm();
      } else {
        Alert.alert("오류", result.message || "인쇄에 실패했습니다.");
      }
    } catch (error) {
      Alert.alert("오류", "서버 연결에 실패했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setTotalWeight("");
    setPalletWeight("");
    setPrinter("");
  };

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
        <View style={styles.inputGroup}>
          <Text style={styles.label}>총무게 (kg) *</Text>
          <TextInput
            style={styles.input}
            value={totalWeight}
            onChangeText={setTotalWeight}
            placeholder="총무게를 입력하세요"
            keyboardType="numeric"
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
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>순수무게 (kg)</Text>
          <View style={styles.displayField}>
            <Text style={styles.displayText}>{netWeight.toFixed(2)} kg</Text>
          </View>
        </View>

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
                    printer === printerName && styles.printerButtonTextSelected,
                  ]}
                >
                  {printerName}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <TouchableOpacity
          style={[styles.printButton, isLoading && styles.printButtonDisabled]}
          onPress={handlePrint}
          disabled={isLoading}
        >
          {isLoading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <>
              <Ionicons name="print" size={20} color="#fff" />
              <Text style={styles.printButtonText}>라벨 인쇄</Text>
            </>
          )}
        </TouchableOpacity>

        <TouchableOpacity style={styles.resetButton} onPress={resetForm}>
          <Ionicons name="refresh" size={20} color="#fff" />
          <Text style={styles.resetButtonText}>초기화</Text>
        </TouchableOpacity>
      </View>
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
    marginBottom: 10,
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
  resetButton: {
    backgroundColor: "#f44336",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    padding: 15,
    borderRadius: 8,
  },
  resetButtonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
    marginLeft: 8,
  },
});
