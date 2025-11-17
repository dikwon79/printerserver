import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";
import LabelPrintScreen from "./screens/LabelPrintScreen";

export default function App() {
  return (
    <SafeAreaProvider>
      <View style={styles.container}>
        <LabelPrintScreen />
      </View>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f5f5f5",
  },
});
