export type ThreadSize = {
  nps: number;
  label: string;
  tpi: number;
  handTight: number;
  effective: number;
  totalThread: number;
  tapDrill: string;
  wrenchTurns: number;
};

export const NPT_TABLE: ThreadSize[] = [
  { nps: 0.125, label: '1/8"', tpi: 27, handTight: 0.1615, effective: 0.2638, totalThread: 0.3924, tapDrill: 'R (0.339")', wrenchTurns: 2.5 },
  { nps: 0.25, label: '1/4"', tpi: 18, handTight: 0.2278, effective: 0.4018, totalThread: 0.5946, tapDrill: '7/16"', wrenchTurns: 2.5 },
  { nps: 0.375, label: '3/8"', tpi: 18, handTight: 0.24, effective: 0.4078, totalThread: 0.6006, tapDrill: '37/64"', wrenchTurns: 2.5 },
  { nps: 0.5, label: '1/2"', tpi: 14, handTight: 0.32, effective: 0.5337, totalThread: 0.7815, tapDrill: '23/32"', wrenchTurns: 3 },
  { nps: 0.75, label: '3/4"', tpi: 14, handTight: 0.339, effective: 0.5457, totalThread: 0.7935, tapDrill: '59/64"', wrenchTurns: 3 },
  { nps: 1, label: '1"', tpi: 11.5, handTight: 0.4, effective: 0.6828, totalThread: 0.9845, tapDrill: '1 5/32"', wrenchTurns: 3 },
  { nps: 1.25, label: '1-1/4"', tpi: 11.5, handTight: 0.42, effective: 0.7068, totalThread: 1.0085, tapDrill: '1 1/2"', wrenchTurns: 3 },
  { nps: 1.5, label: '1-1/2"', tpi: 11.5, handTight: 0.42, effective: 0.7235, totalThread: 1.0252, tapDrill: '1 47/64"', wrenchTurns: 3 },
  { nps: 2, label: '2"', tpi: 11.5, handTight: 0.436, effective: 0.7565, totalThread: 1.0582, tapDrill: '2 7/32"', wrenchTurns: 3 },
  { nps: 2.5, label: '2-1/2"', tpi: 8, handTight: 0.682, effective: 1.1375, totalThread: 1.5712, tapDrill: '2 5/8"', wrenchTurns: 3 },
  { nps: 3, label: '3"', tpi: 8, handTight: 0.766, effective: 1.2, totalThread: 1.6337, tapDrill: '3 1/4"', wrenchTurns: 3 },
  { nps: 4, label: '4"', tpi: 8, handTight: 0.844, effective: 1.3, totalThread: 1.7337, tapDrill: '4 1/4"', wrenchTurns: 3 },
  { nps: 6, label: '6"', tpi: 8, handTight: 0.958, effective: 1.5125, totalThread: 1.9462, tapDrill: '6 5/16"', wrenchTurns: 3 },
];

export type ThreadInput = {
  nps: number;
  turnsPastHandTight: number;
  fittingsPerJoint: number;
};

export type ThreadResult = {
  valid: boolean;
  error?: string;
  size: ThreadSize;
  pitch: number;
  makeupPerTurn: number;
  wrenchMakeup: number;
  totalEngagement: number;
  takeoutPerFitting: number;
  remainingThread: number;
  overThreaded: boolean;
};

export function solveThread(input: ThreadInput): ThreadResult {
  const size = NPT_TABLE.find((t) => t.nps === input.nps) ?? NPT_TABLE[8]!;
  const pitch = 1 / size.tpi;
  const turns = Number.isFinite(input.turnsPastHandTight) ? input.turnsPastHandTight : size.wrenchTurns;
  const wrenchMakeup = turns * pitch;
  const totalEngagement = size.handTight + wrenchMakeup;
  const remainingThread = size.totalThread - totalEngagement;

  return {
    valid: true,
    size,
    pitch,
    makeupPerTurn: pitch,
    wrenchMakeup,
    totalEngagement,
    takeoutPerFitting: totalEngagement,
    remainingThread,
    overThreaded: remainingThread < 0,
    error: remainingThread < 0 ? 'Makeup exceeds available thread — reduce wrench turns or re-cut the thread.' : undefined,
  };
}
