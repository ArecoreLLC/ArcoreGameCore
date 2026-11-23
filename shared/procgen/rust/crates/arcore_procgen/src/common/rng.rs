//! Deterministic randomness. Every stage derives an independent stream from the
//! recipe seed plus stable salts (layer id, cell index), so results never depend on
//! thread count or iteration order across cells.

#[inline]
pub fn mix64(mut z: u64) -> u64 {
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    z ^ (z >> 31)
}

/// FNV-1a: stable string salt (not a security hash).
pub fn hash_str(s: &str) -> u64 {
    let mut h: u64 = 0xCBF2_9CE4_8422_2325;
    for b in s.bytes() {
        h ^= b as u64;
        h = h.wrapping_mul(0x0000_0100_0000_01B3);
    }
    h
}

#[inline]
pub fn hash3(seed: u64, x: i32, y: i32, z: i32) -> u64 {
    let h = mix64(seed ^ (x as u32 as u64).wrapping_mul(0x8CB9_2BA7_2F3D_8DD7));
    let h = mix64(h ^ (y as u32 as u64).wrapping_mul(0xD6E8_FEB8_6659_FD93));
    mix64(h ^ (z as u32 as u64).wrapping_mul(0xA076_1D64_78BD_642F))
}

/// SplitMix64 stream.
#[derive(Clone, Debug)]
pub struct Rng {
    state: u64,
}

impl Rng {
    pub fn new(seed: u64) -> Self {
        Self { state: mix64(seed ^ 0x9E37_79B9_7F4A_7C15) }
    }

    /// Independent stream for `seed` and an ordered list of salts.
    pub fn derive(seed: u64, salts: &[u64]) -> Self {
        let mut h = mix64(seed);
        for s in salts {
            h = mix64(h ^ s.wrapping_mul(0x9E37_79B9_7F4A_7C15));
        }
        Self::new(h)
    }

    pub fn next_u64(&mut self) -> u64 {
        self.state = self.state.wrapping_add(0x9E37_79B9_7F4A_7C15);
        mix64(self.state)
    }

    /// Uniform in `[0, 1)`.
    pub fn next_f32(&mut self) -> f32 {
        (self.next_u64() >> 40) as f32 * (1.0 / (1u64 << 24) as f32)
    }

    pub fn range(&mut self, lo: f32, hi: f32) -> f32 {
        lo + (hi - lo) * self.next_f32()
    }
}

/// Seed for a named sub-stream of the recipe seed.
pub fn sub_seed(seed: u64, name: &str) -> u64 {
    mix64(seed ^ hash_str(name))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn streams_are_reproducible_and_bounded() {
        let mut a = Rng::derive(7, &[1, 2]);
        let mut b = Rng::derive(7, &[1, 2]);
        let mut c = Rng::derive(7, &[2, 1]);
        let mut differs = false;
        for _ in 0..1000 {
            let (x, y, z) = (a.next_f32(), b.next_f32(), c.next_f32());
            assert_eq!(x, y);
            assert!((0.0..1.0).contains(&x));
            differs |= x != z;
        }
        assert!(differs, "salt order must matter");
    }
}
