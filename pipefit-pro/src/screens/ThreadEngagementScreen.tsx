import React, { useMemo, useState } from 'react';
import { Screen } from '../components/Screen';
import { HintRow } from '../components/HintRow';
import { SectionHeader } from '../components/SectionHeader';
import { DimensionInput, FieldRow } from '../components/DimensionInput';
import { ChipRow } from '../components/ChipRow';
import { ControlRow, GhostButton } from '../components/Buttons';
import { FooterNote, MetaBar, ResultBanner, StatGrid, WarningBanner } from '../components/Results';
import { useUnits } from '../hooks/useUnits';
import { NPT_TABLE, solveThread } from '../calc/thread';
import { parseNumber } from '../calc/format';

export function ThreadEngagementScreen() {
  const u = useUnits();
  const [nps, setNps] = useState(2);
  const [turns, setTurns] = useState('');
  const [c2c, setC2c] = useState('');

  const result = useMemo(
    () =>
      solveThread({
        nps,
        turnsPastHandTight: Number.isFinite(parseNumber(turns))
          ? parseNumber(turns)
          : (NPT_TABLE.find((s) => s.nps === nps)?.wrenchTurns ?? 3),
        fittingsPerJoint: 2,
      }),
    [nps, turns]
  );

  const c2cInches = u.parse(c2c);
  const cutLength = Number.isFinite(c2cInches) ? c2cInches - 2 * result.takeoutPerFitting : NaN;

  return (
    <Screen>
      <HintRow text="Work out how far a threaded joint pulls up. Pick the size, set your wrench turns; get engagement, takeout per fitting and the pipe length to cut." />
      <SectionHeader title="Thread" meta="NPT — ASME B1.20.1" />

      <ChipRow
        label="Size"
        options={NPT_TABLE.map((s) => ({ value: s.nps, label: s.label }))}
        selected={nps}
        onSelect={setNps}
      />

      <FieldRow>
        <DimensionInput
          label="Wrench turns"
          value={turns}
          onChangeText={setTurns}
          placeholder={String(result.size.wrenchTurns)}
          suffix="turns"
        />
        <DimensionInput
          label="C2C length"
          value={c2c}
          onChangeText={setC2c}
          suffix={u.suffix}
          placeholder="0"
          readout={u.frac(c2cInches)}
        />
      </FieldRow>

      <ControlRow>
        <GhostButton
          label="Clear all"
          icon="refresh-outline"
          onPress={() => {
            setTurns('');
            setC2c('');
            setNps(2);
          }}
          style={{ flex: 1 }}
        />
      </ControlRow>

      <ResultBanner
        label={Number.isFinite(cutLength) ? 'Pipe cut' : 'Takeout per fitting'}
        value={
          Number.isFinite(cutLength)
            ? `${u.num(cutLength)} ${u.unitName}`
            : `${u.num(result.takeoutPerFitting)} ${u.unitName}`
        }
        hint={
          Number.isFinite(cutLength)
            ? `C2C minus two fittings at ${u.num(result.takeoutPerFitting)} ${u.unitName}`
            : `Hand tight ${u.num(result.size.handTight)} + ${u.num(result.wrenchMakeup)} wrench makeup`
        }
      />

      <MetaBar text={`${result.size.label} NPT · ${result.size.tpi} TPI · Tap drill ${result.size.tapDrill}`} />

      {result.overThreaded ? <WarningBanner text={result.error ?? ''} tone="danger" /> : null}

      <StatGrid
        stats={[
          { label: 'Hand tight', note: 'L1 engagement', value: u.dual(result.size.handTight) },
          { label: 'Wrench makeup', note: `${turns || result.size.wrenchTurns} turns`, value: u.dual(result.wrenchMakeup) },
          { label: 'Total engagement', value: u.dual(result.totalEngagement) },
          { label: 'Thread remaining', value: u.dual(result.remainingThread) },
          { label: 'Pitch', note: 'Per turn', value: u.num(result.pitch, 4) },
          { label: 'Effective thread', note: 'L2 length', value: u.dual(result.size.effective) },
        ]}
      />

      <FooterNote text="Values follow ASME B1.20.1 NPT. Takeout assumes the fitting is made up to the standard wrench-tight position." />
    </Screen>
  );
}
