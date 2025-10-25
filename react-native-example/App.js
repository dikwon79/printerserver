import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { Ionicons } from "@expo/vector-icons";
import LabelPrintScreen from "./screens/LabelPrintScreen";
import BatchPrintScreen from "./screens/BatchPrintScreen";

const Tab = createBottomTabNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <Tab.Navigator
        screenOptions={({ route }) => ({
          tabBarIcon: ({ focused, color, size }) => {
            let iconName;

            if (route.name === "Single") {
              iconName = focused ? "print" : "print-outline";
            } else if (route.name === "Batch") {
              iconName = focused ? "layers" : "layers-outline";
            }

            return <Ionicons name={iconName} size={size} color={color} />;
          },
          tabBarActiveTintColor: "#4CAF50",
          tabBarInactiveTintColor: "gray",
          headerStyle: {
            backgroundColor: "#4CAF50",
          },
          headerTintColor: "#fff",
          headerTitleStyle: {
            fontWeight: "bold",
          },
        })}
      >
        <Tab.Screen
          name="Single"
          component={LabelPrintScreen}
          options={{ title: "단일 인쇄" }}
        />
        <Tab.Screen
          name="Batch"
          component={BatchPrintScreen}
          options={{ title: "일괄 인쇄" }}
        />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
