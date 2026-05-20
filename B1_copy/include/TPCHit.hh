#include "G4Allocator.hh"
#include "G4THitsCollection.hh"
#include "G4ThreeVector.hh"
#include "G4UnitsTable.hh"
#include "G4VHit.hh"

class TPCHit : public G4VHit
{
  public:
    TPCHit() = default;
    ~TPCHit() override = default;
    void Print() override;
    void SetEdep(double const e) { feDep = e; }
    void SetPos(G4ThreeVector xyz) { fPos = xyz; }
    void SetTrackID(G4int track) { fTrackID = track; }
    void SetPDGID(G4int code) { fPDGID = code; }

    /// double is a data type
    G4double GetEdep() const { return feDep; }
    G4ThreeVector GetPos() const { return fPos; }
    G4int GetTrackID() const { return fTrackID; }
    G4int GetPDGID() const { return fPDGID; }

  private:
    G4double feDep;  /// energy deposition
    G4ThreeVector fPos;
    G4int fTrackID;
    G4int fPDGID;
};

using TPCHitCollection = G4THitsCollection<TPCHit>;

extern G4ThreadLocal G4Allocator<TPCHit>* TPCHitAllocator;