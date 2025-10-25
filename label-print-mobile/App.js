import React from "react";
import { View, Text, StyleSheet } from "react-native";
import LabelPrintScreen from "./screens/LabelPrintScreen";

export default function App() {
  return (
    <View style={styles.container}>
      <LabelPrintScreen />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f5f5f5",
  },
});
