import { rad } from './units';

export type SaddleType = 'three' | 'four';

export type SaddleInput = {
  type: SaddleType;
  depth: number;
  width: number;
  distanceToObstruction: number;
  centerAngle: number;
  benderTakeUp: number;
};

export type SaddleMark = {
  label: string;
  position: number;
  angle: number;
  note: string;
};

export type SaddleResult = {
  valid: boolean;
  error?: string;
  multiplier: number;
  shrink: number;
  marks: SaddleMark[];
  developedLength: number;
};

const SHRINK_PER_INCH: Record<number, number> = { 45: 0.1875, 30: 0.125, 22.5: 0.09375 };

export function saddleMultiplier(sideAngle: number): number {
  return 1 / Math.sin(rad(sideAngle));
}

export function solveSaddle(input: SaddleInput): SaddleResult {
  const { depth, distanceToObstruction, centerAngle } = input;
  const empty: SaddleResult = { valid: false, multiplier: NaN, shrink: NaN, marks: [], developedLength: NaN };

  if (!Number.isFinite(depth) || depth <= 0) return { ...empty, error: 'Enter an obstruction depth greater than zero.' };
  if (!Number.isFinite(distanceToObstruction) || distanceToObstruction <= 0)
    return { ...empty, error: 'Enter the distance from the conduit end to the obstruction.' };

  const shrinkRate = SHRINK_PER_INCH[centerAngle] ?? 0.1875;

  if (input.type === 'three') {
    const sideAngle = centerAngle / 2;
    const multiplier = saddleMultiplier(sideAngle);
    const spacing = depth * multiplier;
    const shrink = depth * shrinkRate;
    const center = distanceToObstruction + shrink;
    return {
      valid: true,
      multiplier,
      shrink,
      developedLength: spacing * 2,
      marks: [
        { label: 'Mark 1', position: center - spacing, angle: sideAngle, note: 'Bend away from centre mark' },
        { label: 'Centre', position: center, angle: centerAngle, note: 'Bend over the obstruction' },
        { label: 'Mark 3', position: center + spacing, angle: sideAngle, note: 'Bend away from centre mark' },
      ],
    };
  }

  if (!Number.isFinite(input.width) || input.width <= 0)
    return { ...empty, error: 'Enter the obstruction width for a four-point saddle.' };

  const multiplier = saddleMultiplier(centerAngle);
  const spacing = depth * multiplier;
  const shrink = depth * shrinkRate * 2;
  const first = distanceToObstruction + shrink / 2;
  return {
    valid: true,
    multiplier,
    shrink,
    developedLength: spacing * 2 + input.width,
    marks: [
      { label: 'Mark 1', position: first, angle: centerAngle, note: 'First offset — up' },
      { label: 'Mark 2', position: first + spacing, angle: centerAngle, note: 'First offset — level' },
      { label: 'Mark 3', position: first + spacing + input.width, angle: centerAngle, note: 'Second offset — down' },
      { label: 'Mark 4', position: first + spacing * 2 + input.width, angle: centerAngle, note: 'Second offset — level' },
    ],
  };
}
