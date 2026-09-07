import { solveOffset } from '../calc/offset';
import { solveRolling } from '../calc/rolling';
import { solveCutLength } from '../calc/cutLength';
import { solveSaddle } from '../calc/saddle';
import { solveMiter } from '../calc/miter';
import { solveThread } from '../calc/thread';
import { solveBender } from '../calc/bender';
import { backArc, centerlineArc, findSize, pipeWeightPerFoot, takeoff, throatArc } from '../calc/pipe';
import { parseNumber, toFraction } from '../calc/format';

const near = (a: number, b: number, tol = 0.005) => expect(Math.abs(a - b)).toBeLessThanOrEqual(tol);

describe('elbow geometry against ASME 2" LR', () => {
  const od = findSize(2).od;

  test('setback', () => near(takeoff(2, 'LR', 45), 1.2426));
  test('centreline arc', () => near(centerlineArc(2, 'LR', 45), 2.3562));
  test('throat arc', () => near(throatArc(2, 'LR', 45, od), 1.4235));
  test('back arc', () => near(backArc(2, 'LR', 45, od), 3.2887));
  test('90 LR takeout equals 1.5D', () => near(takeoff(2, 'LR', 90), 3.0));
  test('45 LR takeout matches published 0.625D within rounding', () =>
    near(takeoff(2, 'LR', 45) / 2, 0.625, 0.008));
});

describe('pipe weight', () => {
  test('2 inch SCH40 is 3.65 lb per foot', () => near(pipeWeightPerFoot(2.375, 0.154), 3.653, 0.01));
  test('6 inch SCH40 is 18.97 lb per foot', () => near(pipeWeightPerFoot(6.625, 0.28), 18.974, 0.02));
});

describe('simple offset — reference screenshot 10 x 10 at 45 degrees', () => {
  const r = solveOffset({
    offset: 10,
    fittingAngle: 45,
    gap: 0,
    nps: 2,
    kind: 'LR',
    schedule: '40',
    lockRun: false,
  });

  test('solves', () => expect(r.valid).toBe(true));
  test('run 10.00', () => near(r.run, 10));
  test('travel 14.14', () => near(r.travel, 14.1421));
  test('pipe cut 11.66', () => near(r.pipeCut, 11.6569));
  test('setback 1.24', () => near(r.setback, 1.2426));
  test('throat 1.42', () => near(r.throatArc, 1.4235));
  test('back 3.29', () => near(r.backArc, 3.2887));
  test('centreline arc 2.36', () => near(r.centerlineArc, 2.3562));
  test('pipe weight 3.55 lb', () => near(r.spoolPipe, 3.548, 0.02));
  test('shrink equals travel minus run', () => near(r.shrink, 4.1421));
});

describe('simple offset — run locked drives the angle', () => {
  const r = solveOffset({
    offset: 6,
    run: 12,
    fittingAngle: 45,
    gap: 0,
    nps: 2,
    kind: 'LR',
    schedule: '40',
    lockRun: true,
  });
  test('angle from atan(6/12)', () => near(r.cutAngle, 26.5651));
  test('travel from hypot', () => near(r.travel, 13.4164));
});

describe('simple offset — guards', () => {
  test('rejects zero offset', () => expect(solveOffset({ offset: 0, fittingAngle: 45, gap: 0, nps: 2, kind: 'LR', schedule: '40', lockRun: false }).valid).toBe(false));
  test('rejects takeoffs longer than travel', () => {
    const r = solveOffset({ offset: 1, fittingAngle: 45, gap: 0, nps: 12, kind: 'LR', schedule: '40', lockRun: false });
    expect(r.valid).toBe(false);
    expect(r.error).toMatch(/exceed/i);
  });
});

describe('rolling offset — reference screenshot rise 12 roll 5 run 36', () => {
  const r = solveRolling({
    rise: 12,
    roll: 5,
    run: 36,
    useFittingAngle: false,
    gap: 0,
    nps: 2,
    kind: 'LR',
    schedule: '40',
  });

  test('solves', () => expect(r.valid).toBe(true));
  test('true offset 13.00', () => near(r.trueOffset, 13));
  test('travel 38.28', () => near(r.travel, 38.2753));
  test('required elbow 19.86 degrees', () => near(r.cutAngle, 19.8558, 0.01));
  test('roll angle 22.6 degrees', () => near(r.rollAngle, 22.6199, 0.01));
  test('setback 0.53', () => near(r.setback, 0.5252));
  test('pipe cut 37.23', () => near(r.pipeCut, 37.2249, 0.01));
  test('pipe weight 11.3 lb', () => near(r.spoolPipe, 11.33, 0.05));
});

describe('rolling offset — stock elbow mode solves the run', () => {
  const r = solveRolling({
    rise: 12,
    roll: 5,
    fittingAngle: 45,
    useFittingAngle: true,
    gap: 0,
    nps: 2,
    kind: 'LR',
    schedule: '40',
  });
  test('run equals true offset at 45 degrees', () => near(r.run, 13));
  test('travel is offset times root two', () => near(r.travel, 18.3848));
});

describe('cut length', () => {
  test('two 90 LR elbows on 2 inch, 24 inch C2C', () => {
    const r = solveCutLength({
      centerToCenter: 24,
      endA: 'elbow90',
      endB: 'elbow90',
      customA: NaN,
      customB: NaN,
      gap: 0,
      nps: 2,
      kind: 'LR',
      schedule: '40',
    });
    near(r.takeoffA, 3);
    near(r.pipeCut, 18);
  });

  test('weld gap is applied once per welded end', () => {
    const r = solveCutLength({
      centerToCenter: 24,
      endA: 'elbow90',
      endB: 'none',
      customA: NaN,
      customB: NaN,
      gap: 0.125,
      nps: 2,
      kind: 'LR',
      schedule: '40',
    });
    near(r.totalDeduction, 3.125);
    near(r.pipeCut, 20.875);
  });

  test('rejects when deductions swallow the dimension', () => {
    const r = solveCutLength({
      centerToCenter: 2,
      endA: 'elbow90',
      endB: 'elbow90',
      customA: NaN,
      customB: NaN,
      gap: 0,
      nps: 2,
      kind: 'LR',
      schedule: '40',
    });
    expect(r.valid).toBe(false);
  });
});

describe('saddle bend', () => {
  const r = solveSaddle({ type: 'three', depth: 4, width: NaN, distanceToObstruction: 30, centerAngle: 45, benderTakeUp: 0 });

  test('multiplier at 22.5 side bends is 2.6', () => near(r.multiplier, 2.6131, 0.001));
  test('centre mark carries the shrink', () => near(r.marks[1]!.position, 30.75));
  test('outer marks are 2.6 x depth from centre', () => near(r.marks[2]!.position - r.marks[1]!.position, 10.4525, 0.001));
  test('three marks', () => expect(r.marks).toHaveLength(3));

  test('four point needs a width', () => {
    const bad = solveSaddle({ type: 'four', depth: 4, width: NaN, distanceToObstruction: 30, centerAngle: 45, benderTakeUp: 0 });
    expect(bad.valid).toBe(false);
  });

  test('four point returns four marks', () => {
    const good = solveSaddle({ type: 'four', depth: 4, width: 6, distanceToObstruction: 30, centerAngle: 45, benderTakeUp: 0 });
    expect(good.marks).toHaveLength(4);
    near(good.multiplier, 1.4142);
  });
});

describe('miter bend', () => {
  const r = solveMiter({ totalAngle: 90, segments: 3, nps: 6, schedule: '40', centerlineRadius: 9 });

  test('two cuts for three segments', () => expect(r.cuts).toBe(2));
  test('cut angle is total over twice the cuts', () => near(r.cutAngle, 22.5));
  test('mid segment is twice the cut angle', () => near(r.midSegmentAngle, 45));
  test('throat shorter than back', () => expect(r.throatLength).toBeLessThan(r.backLength));
  test('no code warning at exactly 22.5', () => expect(r.codeWarning).toBeUndefined());

  test('warns above 22.5 degrees', () => {
    const w = solveMiter({ totalAngle: 90, segments: 2, nps: 6, schedule: '40', centerlineRadius: 9 });
    near(w.cutAngle, 45);
    expect(w.codeWarning).toMatch(/B31\.3/);
  });

  test('rejects radius inside the pipe wall', () => {
    expect(solveMiter({ totalAngle: 90, segments: 3, nps: 6, schedule: '40', centerlineRadius: 2 }).valid).toBe(false);
  });
});

describe('thread engagement', () => {
  const r = solveThread({ nps: 2, turnsPastHandTight: 3, fittingsPerJoint: 2 });

  test('pitch is one over TPI', () => near(r.pitch, 1 / 11.5, 0.0001));
  test('wrench makeup is turns times pitch', () => near(r.wrenchMakeup, 3 / 11.5, 0.0001));
  test('total engagement adds hand tight', () => near(r.totalEngagement, 0.436 + 3 / 11.5, 0.0001));
  test('flags over-threading', () => {
    const over = solveThread({ nps: 2, turnsPastHandTight: 20, fittingsPerJoint: 2 });
    expect(over.overThreaded).toBe(true);
  });
});

describe('hand bender', () => {
  const r = solveBender({ angle: 90, radius: 4, takeUp: 5, stubHeight: 12 });

  test('setback at 90 equals the radius', () => near(r.setback, 4));
  test('arc length is R theta', () => near(r.arcLength, 6.2832));
  test('gain is tangents minus arc', () => near(r.gain, 1.7168));
  test('stub mark is height minus take-up', () => near(r.stubMark, 7));
  test('rejects a zero radius', () => expect(solveBender({ angle: 90, radius: 0, takeUp: 5, stubHeight: 12 }).valid).toBe(false));
});

describe('input parsing and fraction readout', () => {
  test('parses a mixed fraction', () => near(parseNumber('11 5/8'), 11.625));
  test('parses a bare fraction', () => near(parseNumber('3/16'), 0.1875));
  test('parses a decimal with an inch mark', () => near(parseNumber('14.14"'), 14.14));
  test('rejects junk', () => expect(Number.isNaN(parseNumber('abc'))).toBe(true));
  test('renders sixteenths', () => expect(toFraction(11.6569, 16)).toBe('11 11/16"'));
  test('reduces the fraction', () => expect(toFraction(0.5, 16)).toBe('1/2"'));
  test('rolls up to the next whole number', () => expect(toFraction(2.999, 16)).toBe('3"'));
  test('returns empty when fractions are off', () => expect(toFraction(1.5, 0)).toBe(''));
});
