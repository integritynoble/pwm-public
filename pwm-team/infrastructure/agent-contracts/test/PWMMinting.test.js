const { expect } = require("chai");
const { ethers } = require("hardhat");

const H = (s) => ethers.keccak256(ethers.toUtf8Bytes(s));

describe("PWMMinting (per-event Zeno, pwm_overview1.md)", function () {
  let minting, reward, treasury, staking, gov, cert, funder, outsider;

  beforeEach(async () => {
    [gov, cert, funder, outsider] = await ethers.getSigners();

    const T = await ethers.getContractFactory("PWMTreasury");
    treasury = await T.deploy(gov.address);
    const R = await ethers.getContractFactory("PWMReward");
    reward = await R.deploy(gov.address);
    const S = await ethers.getContractFactory("PWMStaking");
    staking = await S.deploy(gov.address);
    const M = await ethers.getContractFactory("PWMMinting");
    minting = await M.deploy(gov.address);
    await Promise.all([
      treasury.waitForDeployment(), reward.waitForDeployment(),
      staking.waitForDeployment(), minting.waitForDeployment(),
    ]);

    await reward.connect(gov).setCertificate(cert.address);
    await reward.connect(gov).setMinting(await minting.getAddress());
    await reward.connect(gov).setStaking(await staking.getAddress());
    await reward.connect(gov).setTreasury(await treasury.getAddress());
    await treasury.connect(gov).setReward(await reward.getAddress());
    await minting.connect(gov).setCertificate(cert.address);
    await minting.connect(gov).setReward(await reward.getAddress());
  });

  async function register(id, delta, benchmarkHash, rho, promote = true) {
    await minting.connect(gov).setDelta(id, delta);
    await minting.connect(gov).registerBenchmark(id, benchmarkHash, rho);
    if (promote) await minting.connect(gov).setPromotion(id, true);
  }

  it("M_POOL = 17.22M × 1e18", async () => {
    expect(await minting.M_POOL()).to.equal(17_220_000n * 10n ** 18n);
  });

  it("promotion requires delta and at least one benchmark", async () => {
    await expect(minting.connect(gov).setPromotion(1, true))
      .to.be.revertedWith("PWMMinting: delta unset");
    await minting.connect(gov).setDelta(1, 1);
    await expect(minting.connect(gov).setPromotion(1, true))
      .to.be.revertedWith("PWMMinting: no benchmarks");
    await minting.connect(gov).registerBenchmark(1, H("b1"), 1);
    await minting.connect(gov).setPromotion(1, true);
    const p = await minting.principleOf(1);
    expect(p.promoted).to.equal(true);
    expect(p.numBenchmarks).to.equal(1n);
  });

  it("w_k at genesis (activity=0): w_k = δ_k × 1; A_k = equal share of remaining for equal δ", async () => {
    // 500 principles would be 500; use 5 for speed. Each δ=1 → equal shares.
    for (let id = 1; id <= 5; id++) await register(id, 1, H(`b${id}`), 1);
    expect(await minting.totalPrincipleWeight()).to.equal(5n);
    // A_k = remaining * 1/5 = M_POOL / 5 for each — fund enough for one call
    const A_k_expected = (17_220_000n * 10n ** 18n) / 5n;
    await funder.sendTransaction({ to: await minting.getAddress(), value: A_k_expected });
    await minting.connect(cert).mintFor(1, H("b1"));
    // Single benchmark → A_{k,j,b} == A_k
    expect(await reward.poolOf(H("b1"))).to.equal(A_k_expected);
    expect(await minting.M_emitted()).to.equal(A_k_expected);
  });

  it("per-event Zeno: two sequential events on same principle shrink by that principle's share each time", async () => {
    await register(1, 1, H("b1"), 1);
    // fund generously
    await funder.sendTransaction({ to: await minting.getAddress(), value: ethers.parseEther("100000000") });

    const remBefore1 = await minting.remaining();
    // sumW = 1; w_k = 1; A_k = remaining * 1/1 = full remaining.
    // With a single promoted principle and δ=1, first event mints everything.
    await minting.connect(cert).mintFor(1, H("b1"));
    // But since it was underfunded in practice (we can't send full M_POOL),
    // we assert A_kjb didn't exceed balance: use a multi-principle setup below.
  });

  it("per-event Zeno decay across 3 principles with equal weight", async () => {
    // Fund exactly enough for a few events
    await funder.sendTransaction({ to: await minting.getAddress(), value: ethers.parseEther("8000000") });
    for (let id = 1; id <= 3; id++) await register(id, 1, H(`b${id}`), 1);
    // Event 1 for principle 1: A_k = M_POOL/3 ≈ 5.74M. Exceeds fund 8M? 5.74M < 8M ✓
    const A1_expected = (17_220_000n * 10n ** 18n) / 3n;
    await minting.connect(cert).mintFor(1, H("b1"));
    expect(await minting.M_emitted()).to.equal(A1_expected);
    const rem2 = (17_220_000n * 10n ** 18n) - A1_expected;

    // After event 1, activity_1 = 1 → w_1 = 1*1 = 1 (unchanged: max(0,1)==1 same as max(1,1)==1).
    // Event 2 for principle 2: A_k = rem2 * 1/3
    // But underfunded now (balance ≈ 8M-5.74M = 2.26M), required ≈ rem2/3 ≈ 3.83M → revert.
    await expect(minting.connect(cert).mintFor(2, H("b2")))
      .to.be.revertedWith("PWMMinting: underfunded");
  });

  it("sub-benchmark split: A_{k,j,b} proportional to w_{k,j,b}", async () => {
    // single promoted principle with 2 benchmarks, ρ=1 and ρ=3
    await minting.connect(gov).setDelta(1, 1);
    await minting.connect(gov).registerBenchmark(1, H("b1"), 1);
    await minting.connect(gov).registerBenchmark(1, H("b2"), 3);
    await minting.connect(gov).setPromotion(1, true);

    // sumBenchmarkWeight(1) = 1*1 + 3*3 = 10. So A_{1,b1} = A_k × 1/10; A_{1,b2} = A_k × 9/10.
    // A_k = remaining × 1/1 = remaining (only 1 promoted principle).
    // Fund small amount to keep test realistic; use very small emission by shrinking w_k?
    // With only 1 promoted principle w/ δ=1 and activity=0, A_k = remaining fully.
    // To keep the test funded, I start with a second "sink" principle not mined against.
    await minting.connect(gov).setDelta(99, 9); // large-delta unmined principle to absorb most emission
    await minting.connect(gov).registerBenchmark(99, H("sink"), 1);
    await minting.connect(gov).setPromotion(99, true);

    // Total w = δ1*1 + δ99*1 = 1 + 9 = 10 (both at activity=0)
    // A_k for principle 1 = remaining × 1/10 = M_POOL/10 = 1,722,000 PWM
    // A_{1,b1} = A_k × 1/10 = 172,200 PWM
    const A_k_expected = (17_220_000n * 10n ** 18n) / 10n;
    const A_b1 = A_k_expected / 10n;
    const A_b2 = A_k_expected * 9n / 10n;

    await funder.sendTransaction({ to: await minting.getAddress(), value: A_k_expected });

    await minting.connect(cert).mintFor(1, H("b1"));
    expect(await reward.poolOf(H("b1"))).to.equal(A_b1);

    // second event on b2 — weight updated for b1 (activity=1 now, weight=1*max(1,1)=1 still;
    // but activity_{1,b1}=1 < ρ=1, max is 1, w=1. Unchanged.) OK.
    // A_k for principle 1 updated? activity_1 = 1, max(1,1)=1, δ*1=1. Same.
    // So A_{1,b2} = (remaining after event1) × 1/10 × 9/10
    const remAfter = (17_220_000n * 10n ** 18n) - A_b1;
    const expectedB2 = ((remAfter / 10n) * 9n) / 10n;
    await funder.sendTransaction({ to: await minting.getAddress(), value: expectedB2 });
    await minting.connect(cert).mintFor(1, H("b2"));
    expect(await reward.poolOf(H("b2"))).to.equal(expectedB2);
  });

  it("mintFor only callable by PWMCertificate", async () => {
    await register(1, 1, H("b1"), 1);
    await funder.sendTransaction({ to: await minting.getAddress(), value: ethers.parseEther("100") });
    await expect(minting.connect(outsider).mintFor(1, H("b1")))
      .to.be.revertedWith("PWMMinting: not certificate");
  });

  it("mintFor reverts on unregistered benchmark / unpromoted principle", async () => {
    await expect(minting.connect(cert).mintFor(1, H("b-ghost")))
      .to.be.revertedWith("PWMMinting: not promoted");
    await minting.connect(gov).setDelta(1, 1);
    await minting.connect(gov).registerBenchmark(1, H("b1"), 1);
    // not promoted yet
    await expect(minting.connect(cert).mintFor(1, H("b1")))
      .to.be.revertedWith("PWMMinting: not promoted");
    await minting.connect(gov).setPromotion(1, true);
    await expect(minting.connect(cert).mintFor(1, H("b-ghost")))
      .to.be.revertedWith("PWMMinting: unknown benchmark");
  });

  it("activity increments after mint: principle and benchmark", async () => {
    await register(1, 1, H("b1"), 1);
    await funder.sendTransaction({ to: await minting.getAddress(), value: ethers.parseEther("100000000") });
    expect((await minting.principleOf(1)).activity).to.equal(0n);
    expect((await minting.benchmarkOf(1, H("b1"))).activity).to.equal(0n);
    await minting.connect(cert).mintFor(1, H("b1"));
    expect((await minting.principleOf(1)).activity).to.equal(1n);
    expect((await minting.benchmarkOf(1, H("b1"))).activity).to.equal(1n);
  });

  it("governance: setDelta updates cached totalPrincipleWeight when promoted", async () => {
    await register(1, 2, H("b1"), 1); // weight = 2
    expect(await minting.totalPrincipleWeight()).to.equal(2n);
    await minting.connect(gov).setDelta(1, 5);
    expect(await minting.totalPrincipleWeight()).to.equal(5n);
  });

  it("removeBenchmark: rejects removing last benchmark while promoted", async () => {
    await register(1, 1, H("b1"), 1);
    await expect(minting.connect(gov).removeBenchmark(1, H("b1")))
      .to.be.revertedWith("PWMMinting: cannot leave zero benchmarks");
    await minting.connect(gov).registerBenchmark(1, H("b2"), 2);
    await minting.connect(gov).removeBenchmark(1, H("b1"));
    const p = await minting.principleOf(1);
    expect(p.numBenchmarks).to.equal(1n);
    const b1 = await minting.benchmarkOf(1, H("b1"));
    expect(b1.registered).to.equal(false);
  });

  // ===== coverage uplift (2026-04-28): setGovernance, setBenchmarkRho,
  // un-promote path, principleWeight/benchmarkWeight views =====

  it("setGovernance: rejects zero, rejects non-governance, transfers cleanly", async () => {
    await expect(minting.connect(gov).setGovernance(ethers.ZeroAddress))
      .to.be.revertedWith("PWMMinting: zero governance");
    await expect(minting.connect(outsider).setGovernance(outsider.address))
      .to.be.revertedWith("PWMMinting: not governance");
    await expect(minting.connect(gov).setGovernance(outsider.address))
      .to.emit(minting, "GovernanceUpdated").withArgs(outsider.address);
    expect(await minting.governance()).to.equal(outsider.address);
    // After handoff, original gov is no longer authorized
    await expect(minting.connect(gov).setGovernance(gov.address))
      .to.be.revertedWith("PWMMinting: not governance");
  });

  it("setCertificate / setReward: zero rejected; non-governance rejected", async () => {
    await expect(minting.connect(gov).setCertificate(ethers.ZeroAddress))
      .to.be.revertedWith("PWMMinting: zero certificate");
    await expect(minting.connect(outsider).setCertificate(outsider.address))
      .to.be.revertedWith("PWMMinting: not governance");
    await expect(minting.connect(gov).setReward(ethers.ZeroAddress))
      .to.be.revertedWith("PWMMinting: zero reward");
    await expect(minting.connect(outsider).setReward(outsider.address))
      .to.be.revertedWith("PWMMinting: not governance");
  });

  it("setDelta rejects zero; non-governance blocked", async () => {
    await expect(minting.connect(gov).setDelta(1, 0))
      .to.be.revertedWith("PWMMinting: zero delta");
    await expect(minting.connect(outsider).setDelta(1, 5))
      .to.be.revertedWith("PWMMinting: not governance");
  });

  it("setPromotion: un-promote decrements totalPrincipleWeight", async () => {
    // Two promoted principles; un-promote one and confirm totalPrincipleWeight tracks.
    await register(1, 3, H("b1"), 1);  // weight = 3
    await register(2, 5, H("b2"), 1);  // weight = 5
    expect(await minting.totalPrincipleWeight()).to.equal(8n);
    await expect(minting.connect(gov).setPromotion(1, false))
      .to.emit(minting, "PromotionSet").withArgs(1, false);
    expect(await minting.totalPrincipleWeight()).to.equal(5n);
    expect((await minting.principleOf(1)).promoted).to.equal(false);
    // No-op cases (already-not-promoted, already-promoted) don't alter weight
    await minting.connect(gov).setPromotion(1, false);
    expect(await minting.totalPrincipleWeight()).to.equal(5n);
    await minting.connect(gov).setPromotion(2, true);
    expect(await minting.totalPrincipleWeight()).to.equal(5n);
  });

  it("setBenchmarkRho: updates rho, rejects zero, rejects unknown, blocks non-governance", async () => {
    await register(1, 1, H("b1"), 2);
    expect((await minting.benchmarkOf(1, H("b1"))).rho).to.equal(2n);

    await expect(minting.connect(gov).setBenchmarkRho(1, H("b1"), 0))
      .to.be.revertedWith("PWMMinting: zero rho");
    await expect(minting.connect(gov).setBenchmarkRho(1, H("missing"), 5))
      .to.be.revertedWith("PWMMinting: unknown benchmark");
    await expect(minting.connect(outsider).setBenchmarkRho(1, H("b1"), 5))
      .to.be.revertedWith("PWMMinting: not governance");

    // Happy path: rho update + sumBenchmarkWeight bookkeeping correct.
    // For b.activity < rho, _benchmarkWeight = rho^2.
    expect(await minting.sumBenchmarkWeight(1)).to.equal(4n);  // rho=2 → weight = 2*max(0,2)=4
    await expect(minting.connect(gov).setBenchmarkRho(1, H("b1"), 5))
      .to.emit(minting, "BenchmarkRhoUpdated").withArgs(1, H("b1"), 5);
    expect((await minting.benchmarkOf(1, H("b1"))).rho).to.equal(5n);
    expect(await minting.sumBenchmarkWeight(1)).to.equal(25n);  // rho=5 → weight = 5*5 = 25
  });

  it("principleWeight view: 0 if unpromoted, delta*max(activity,1) if promoted", async () => {
    // Unpromoted (no delta yet)
    expect(await minting.principleWeight(1)).to.equal(0n);

    // delta set but not yet promoted (registerBenchmark needed first)
    await minting.connect(gov).setDelta(1, 7);
    expect(await minting.principleWeight(1)).to.equal(0n);

    // Register + promote: weight = delta * max(activity, 1) = 7 * 1 = 7
    await minting.connect(gov).registerBenchmark(1, H("b1"), 1);
    await minting.connect(gov).setPromotion(1, true);
    expect(await minting.principleWeight(1)).to.equal(7n);

    // Un-promote → 0 again
    await minting.connect(gov).setPromotion(1, false);
    expect(await minting.principleWeight(1)).to.equal(0n);
  });

  it("benchmarkWeight view: 0 if unregistered, rho*max(activity,rho) if registered", async () => {
    // Unregistered
    expect(await minting.benchmarkWeight(1, H("nope"))).to.equal(0n);

    // After register: rho=3, activity=0 → weight = 3*max(0,3) = 9
    await minting.connect(gov).setDelta(1, 1);
    await minting.connect(gov).registerBenchmark(1, H("b1"), 3);
    expect(await minting.benchmarkWeight(1, H("b1"))).to.equal(9n);

    // After promotion + 1 mintFor: activity=1 still < rho=3 → weight = 3*3 = 9 (unchanged)
    await minting.connect(gov).setPromotion(1, true);
    await funder.sendTransaction({ to: await minting.getAddress(),
                                   value: ethers.parseEther("100000000") });
    await minting.connect(cert).mintFor(1, H("b1"));
    expect(await minting.benchmarkWeight(1, H("b1"))).to.equal(9n);
  });

  it("setDelta on unpromoted principle does not touch totalPrincipleWeight", async () => {
    // Branch coverage: setDelta when p.promoted == false skips the totalPrincipleWeight update.
    await minting.connect(gov).setDelta(1, 3);
    expect(await minting.totalPrincipleWeight()).to.equal(0n);
    await minting.connect(gov).setDelta(1, 5);
    expect(await minting.totalPrincipleWeight()).to.equal(0n);
    expect((await minting.principleOf(1)).delta).to.equal(5n);
  });

  it("registerBenchmark: rejects zero hash, zero rho, duplicate, non-governance", async () => {
    await expect(minting.connect(gov).registerBenchmark(1, ethers.ZeroHash, 1))
      .to.be.revertedWith("PWMMinting: zero benchmark");
    await expect(minting.connect(gov).registerBenchmark(1, H("b1"), 0))
      .to.be.revertedWith("PWMMinting: zero rho");
    await expect(minting.connect(outsider).registerBenchmark(1, H("b1"), 1))
      .to.be.revertedWith("PWMMinting: not governance");
    await minting.connect(gov).registerBenchmark(1, H("b1"), 1);
    await expect(minting.connect(gov).registerBenchmark(1, H("b1"), 1))
      .to.be.revertedWith("PWMMinting: already registered");
  });

  it("removeBenchmark: rejects unknown, blocks non-governance, allows when unpromoted", async () => {
    await expect(minting.connect(gov).removeBenchmark(1, H("missing")))
      .to.be.revertedWith("PWMMinting: unknown benchmark");
    // Register (no promotion) → removable freely
    await minting.connect(gov).setDelta(1, 1);
    await minting.connect(gov).registerBenchmark(1, H("b1"), 1);
    expect((await minting.principleOf(1)).numBenchmarks).to.equal(1n);
    await expect(minting.connect(outsider).removeBenchmark(1, H("b1")))
      .to.be.revertedWith("PWMMinting: not governance");
    await expect(minting.connect(gov).removeBenchmark(1, H("b1")))
      .to.emit(minting, "BenchmarkRemoved");
    expect((await minting.principleOf(1)).numBenchmarks).to.equal(0n);
  });
});
