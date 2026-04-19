const { expect } = require("chai");
const { ethers } = require("hardhat");

const H = (s) => ethers.keccak256(ethers.toUtf8Bytes(s));
const ZERO = ethers.ZeroHash;

describe("PWMRegistry", function () {
  let registry, alice, bob;

  beforeEach(async () => {
    [alice, bob] = await ethers.getSigners();
    const F = await ethers.getContractFactory("PWMRegistry");
    registry = await F.deploy();
    await registry.waitForDeployment();
  });

  it("registers an L1 principle and reads it back", async () => {
    const h = H("principle:eikonal");
    await expect(registry.register(h, ZERO, 1, alice.address))
      .to.emit(registry, "ArtifactRegistered");

    const [parent, layer, creator, ts] = await registry.getArtifact(h);
    expect(parent).to.equal(ZERO);
    expect(layer).to.equal(1);
    expect(creator).to.equal(alice.address);
    expect(ts).to.be.gt(0n);
    expect(await registry.exists(h)).to.equal(true);
  });

  it("accepts L1, L2, L3, L4 artifacts with valid parents", async () => {
    const p = H("p"), s = H("s"), b = H("b"), sol = H("sol");
    await registry.register(p, ZERO, 1, alice.address);
    await registry.register(s, p,    2, alice.address);
    await registry.register(b, s,    3, alice.address);
    await registry.register(sol, b,  4, bob.address);
    expect((await registry.getArtifact(sol))[1]).to.equal(4);
  });

  it("reverts on re-registration of same hash", async () => {
    const h = H("dup");
    await registry.register(h, ZERO, 1, alice.address);
    await expect(registry.register(h, ZERO, 1, alice.address))
      .to.be.revertedWith("PWMRegistry: already registered");
  });

  it("reverts on invalid layer", async () => {
    await expect(registry.register(H("x"), ZERO, 0, alice.address))
      .to.be.revertedWith("PWMRegistry: invalid layer");
    await expect(registry.register(H("y"), ZERO, 5, alice.address))
      .to.be.revertedWith("PWMRegistry: invalid layer");
  });

  it("reverts on zero hash / zero creator", async () => {
    await expect(registry.register(ZERO, ZERO, 1, alice.address))
      .to.be.revertedWith("PWMRegistry: zero hash");
    await expect(registry.register(H("a"), ZERO, 1, ethers.ZeroAddress))
      .to.be.revertedWith("PWMRegistry: zero creator");
  });

  it("L1 must have zero parent; L2+ must reference a registered parent", async () => {
    await expect(registry.register(H("bad-root"), H("nonexistent"), 1, alice.address))
      .to.be.revertedWith("PWMRegistry: L1 must have zero parent");
    await expect(registry.register(H("orphan"), ZERO, 2, alice.address))
      .to.be.revertedWith("PWMRegistry: parent required");
    await expect(registry.register(H("ghost"), H("unregistered"), 2, alice.address))
      .to.be.revertedWith("PWMRegistry: parent not registered");
  });

  it("exists() is false for unregistered hash", async () => {
    expect(await registry.exists(H("nope"))).to.equal(false);
  });
});
