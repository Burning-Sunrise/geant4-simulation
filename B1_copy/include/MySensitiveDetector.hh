#include "G4VSensitiveDetector.hh"
#include "TPCHit.hh"

/// This is the sensitive detector to track energy, position, time.
/// : inherit
class MySensitiveDetector : public G4VSensitiveDetector
{
  public:
    MySensitiveDetector(G4String SDname);

    ~MySensitiveDetector() override = default;

    /// build a histogram of hits step by step
    G4bool ProcessHits(G4Step* step, G4TouchableHistory* ROhist) override;
    void Initialize(G4HCofThisEvent* HCE) override;
    void EndOfEvent(G4HCofThisEvent* HCE) override;

  private:
    TPCHitCollection* hitCollection;  /// define hitCollection
};

/// we found physics list
/// we set up sensitive detector cc, hit cc.