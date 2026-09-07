import { ElbowRadius, findSize, pipeWeight, Schedule, takeoff } from './pipe';

export type EndFitting =
  | 'none'
  | 'elbow90'
  | 'elbow45'
  | 'tee'
  | 'coupling'
  | 'weldolet'
  | 'flange150'
  | 'flange300'
  | 'custom';

export const END_FITTINGS: { id: EndFitting; label: string }[] = [
  { id: 'none', label: 'Open end' },
  { id: 'elbow90', label: '90° elbow' },
  { id: 'elbow45', label: '45° elbow' },
  { id: 'tee', label: 'Tee (run)' },
  { id: 'coupling', label: 'Coupling' },
  { id: 'weldolet', label: 'Weldolet' },
  { id: 'flange150', label: 'Flange 150#' },
  { id: 'flange300', label: 'Flange 300#' },
  { id: 'custom', label: 'Custom' },
];

const TEE_CENTER_TO_END: Record<number, number> = {
  0.5: 1.0, 0.75: 1.125, 1: 1.5, 1.25: 1.875, 1.5: 2.25, 2: 2.5, 2.5: 3.0, 3: 3.375, 3.5: 3.75,
  4: 4.125, 5: 4.875, 6: 5.625, 8: 7.0, 10: 8.5, 12: 10.0, 14: 11.0, 16: 12.0, 18: 13.5, 20: 15.0, 24: 17.0,
};

const FLANGE_150_LENGTH: Record<number, number> = {
  0.5: 0.5625, 0.75: 0.625, 1: 0.6875, 1.25: 0.8125, 1.5: 0.875, 2: 1.0, 2.5: 1.125, 3: 1.1875,
  3.5: 1.25, 4: 1.25, 5: 1.4375, 6: 1.5625, 8: 1.75, 10: 1.9375, 12: 2.1875, 14: 2.25, 16: 2.5,
  18: 2.6875, 20: 2.875, 24: 3.25,
};

const FLANGE_300_LENGTH: Record<number, number> = {
  0.5: 0.875, 0.75: 1.0, 1: 1.0625, 1.25: 1.0625, 1.5: 1.1875, 2: 1.3125, 2.5: 1.5, 3: 1.6875,
  3.5: 1.75, 4: 1.875, 5: 2.0, 6: 2.0625, 8: 2.4375, 10: 2.625, 12: 2.875, 14: 3.0, 16: 3.25,
  18: 3.5, 20: 3.75, 24: 4.1875,
};

export function endTakeoff(fitting: EndFitting, nps: number, kind: ElbowRadius, custom: number): number {
  switch (fitting) {
    case 'none':
      return 0;
    case 'elbow90':
      return takeoff(nps, kind, 90);
    case 'elbow45':
      return takeoff(nps, kind, 45);
    case 'tee':
      return TEE_CENTER_TO_END[nps] ?? nps * 1.25;
    case 'coupling':
      return 0;
    case 'weldolet':
      return 0;
    case 'flange150':
      return FLANGE_150_LENGTH[nps] ?? nps * 0.4;
    case 'flange300':
      return FLANGE_300_LENGTH[nps] ?? nps * 0.5;
    case 'custom':
      return Number.isFinite(custom) ? custom : 0;
    default:
      return 0;
  }
}

export type CutLengthInput = {
  centerToCenter: number;
  endA: EndFitting;
  endB: EndFitting;
  customA: number;
  customB: number;
  gap: number;
  nps: number;
  kind: ElbowRadius;
  schedule: Schedule;
};

export type CutLengthResult = {
  valid: boolean;
  error?: string;
  takeoffA: number;
  takeoffB: number;
  totalDeduction: number;
  pipeCut: number;
  weight: number;
};

export function solveCutLength(input: CutLengthInput): CutLengthResult {
  const { centerToCenter, gap, nps, kind, schedule } = input;
  const base = {
    takeoffA: endTakeoff(input.endA, nps, kind, input.customA),
    takeoffB: endTakeoff(input.endB, nps, kind, input.customB),
  };
  const gapValue = Number.isFinite(gap) ? gap : 0;
  const weldCount = (input.endA === 'none' ? 0 : 1) + (input.endB === 'none' ? 0 : 1);
  const totalDeduction = base.takeoffA + base.takeoffB + gapValue * weldCount;

  if (!Number.isFinite(centerToCenter) || centerToCenter <= 0) {
    return { valid: false, error: 'Enter a centre-to-centre dimension.', ...base, totalDeduction, pipeCut: NaN, weight: NaN };
  }

  const pipeCut = centerToCenter - totalDeduction;
  const size = findSize(nps);
  return {
    valid: pipeCut > 0,
    error: pipeCut > 0 ? undefined : 'Deductions exceed the centre-to-centre dimension.',
    ...base,
    totalDeduction,
    pipeCut,
    weight: pipeWeight(pipeCut, size.od, size.wall[schedule]),
  };
}
