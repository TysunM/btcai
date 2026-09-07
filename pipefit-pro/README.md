# PipeFit Pro

Field calculators for pipe, tube and conduit. Expo SDK 57 / React Native 0.86 / TypeScript.

## Run

```
npm install
npx expo start
```

## Structure

| Path | Role |
| --- | --- |
| `src/calc/` | Pure calculation modules. No React, no UI imports. Unit tested. |
| `src/theme/` | Design tokens, typography scale, light/dark provider. |
| `src/components/` | Shared UI kit: fields, chips, result banner, stat grid, sheets. |
| `src/screens/` | One file per calculator. Presentation only. |
| `src/hooks/` | Unit formatting and pipe-selection state. |
| `src/state/` | Persisted settings (AsyncStorage). |

## Calculators

Simple offset · Rolling offset · Cut length · Saddle bend · Miter bend · Thread engagement · Hand bender.

## Geometry

All elbow figures derive from the centreline bend radius `R` (1.5×NPS long radius, 1.0×NPS short radius):

- Setback / takeout: `R · tan(θ/2)`
- Centreline arc: `R · θ`
- Throat arc: `(R − OD/2) · θ`
- Back arc: `(R + OD/2) · θ`
- Pipe weight: `10.6802 · t · (OD − t)` lb/ft

Pipe OD and wall thickness follow ASME B36.10M. Tee and flange takeouts follow ASME B16.9 and B16.5. NPT values follow ASME B1.20.1. Miter cut angles are checked against the ASME B31.3 §304.2.3 22.5° threshold.

Fitting weights are geometric estimates, not vendor catalogue figures. They are labelled as estimates in the UI.

## Verification

```
npm run typecheck
npm test
```

65 unit tests, including regression cases pinned to known-good values:

- 10" offset at 45° on 2" LR → travel 14.1421, pipe cut 11.6569, setback 1.2426, throat 1.4235, back 3.2887, arc 2.3562
- Rise 12 / roll 5 / run 36 on 2" LR → true offset 13.00, travel 38.2753, elbow 19.86°, roll 22.62°, pipe cut 37.2249

## Theming

Tokens live in `src/theme/tokens.ts`. Light and dark palettes are complete and independent; every screen reads colours from `useTheme()` and hard-codes none. Theme preference (light / dark / system) persists per device.

## Units

Imperial and metric. Imperial adds an optional fractional readout at 1/8, 1/16, 1/32 or 1/64. The decimal figure is always the exact calculated value; the fraction is a rounded convenience.

Fraction *entry* (`11 5/8`) is parsed by `parseNumber`. On iOS the numeric keyboard includes `/` and space. On Android the decimal pad does not, so fraction entry there requires switching `keyboardType` in `src/components/DimensionInput.tsx`.

## Not built

The header in the reference design carries save and print actions. Those need persistence and `expo-print` and are not implemented — no dead buttons were added in their place.
