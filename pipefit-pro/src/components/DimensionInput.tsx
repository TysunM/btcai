import React from 'react';
import { Platform, StyleSheet, Text, TextInput, View, ViewStyle } from 'react-native';
import { useTheme } from '../theme/ThemeProvider';

export function DimensionInput({
  label,
  value,
  onChangeText,
  suffix,
  placeholder,
  editable = true,
  readout,
  style,
  keyboardType,
}: {
  label: string;
  value: string;
  onChangeText?: (next: string) => void;
  suffix?: string;
  placeholder?: string;
  editable?: boolean;
  readout?: string;
  style?: ViewStyle;
  keyboardType?: 'decimal-pad' | 'numbers-and-punctuation' | 'default';
}) {
  const t = useTheme();
  const kb =
    keyboardType ??
    (Platform.select({ ios: 'numbers-and-punctuation', default: 'decimal-pad' }) as 'decimal-pad');
  return (
    <View style={[{ flex: 1, minWidth: 96 }, style]}>
      <Text style={[t.type.label, { color: t.colors.textMuted, marginBottom: t.space.sm }]} numberOfLines={1}>
        {label}
      </Text>
      <View
        style={[
          styles.box,
          {
            height: t.layout.fieldHeight,
            borderRadius: t.radius.md,
            borderColor: t.colors.border,
            backgroundColor: editable ? t.colors.bgRaised : t.colors.bgSubtle,
            paddingHorizontal: t.space.md,
          },
        ]}
      >
        <TextInput
          value={value}
          onChangeText={onChangeText}
          editable={editable}
          placeholder={placeholder}
          placeholderTextColor={t.colors.textFaint}
          keyboardType={kb}
          inputMode={kb === 'decimal-pad' ? 'decimal' : 'text'}
          selectTextOnFocus
          style={[t.type.fieldValue, { color: t.colors.text, flex: 1, padding: 0 }]}
        />
        {suffix ? <Text style={[t.type.body, { color: t.colors.textFaint }]}>{suffix}</Text> : null}
      </View>
      {readout ? (
        <Text style={[t.type.caption, { color: t.colors.data, marginTop: 6 }]} numberOfLines={1}>
          {readout}
        </Text>
      ) : null}
    </View>
  );
}

export function DerivedField({ label, value, style }: { label: string; value: string; style?: ViewStyle }) {
  const t = useTheme();
  return (
    <View style={[{ flex: 1, minWidth: 96 }, style]}>
      <Text style={[t.type.label, { color: t.colors.textMuted, marginBottom: t.space.sm }]} numberOfLines={1}>
        {label}
      </Text>
      <View
        style={[
          styles.box,
          {
            height: t.layout.fieldHeight,
            borderRadius: t.radius.md,
            borderColor: 'transparent',
            backgroundColor: t.colors.bgSubtle,
            paddingHorizontal: t.space.md,
          },
        ]}
      >
        <Text style={[t.type.fieldValue, { color: t.colors.text }]} numberOfLines={1} adjustsFontSizeToFit>
          {value}
        </Text>
      </View>
    </View>
  );
}

export function FieldRow({ children }: { children: React.ReactNode }) {
  const t = useTheme();
  return (
    <View
      style={{
        flexDirection: 'row',
        gap: t.space.md,
        paddingHorizontal: t.layout.screenPadding,
        marginBottom: t.space.lg,
      }}
    >
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  box: { flexDirection: 'row', alignItems: 'center', borderWidth: 1 },
});
