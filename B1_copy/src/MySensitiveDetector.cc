#include "MySensitiveDetector.hh"

MySensitiveDetector::MySensitiveDetector(G4String SDname)
    : G4VSensitiveDetector(SDname)
{
    G4cout << "Creating SensitiveDetector with name: " << SDname << "\n";
    collectionName.insert("TPCHitCollection");
}

void MySensitiveDetector::Initialize(G4HCofThisEvent* HCE)  // Hit collection
                                                            // of event
{  // initialize hit collection
    hitCollection = new TPCHitCollection(GetName(), collectionName[0]);

    static G4int HCID = -1;
    if (HCID < 0)
        HCID = GetCollectionID(0);
    HCE->AddHitsCollection(HCID, hitCollection);
}
/// ::scope
G4bool
MySensitiveDetector::ProcessHits(G4Step* step, G4TouchableHistory* ROhist)
{
    G4TouchableHandle touchable = step->GetPreStepPoint()->GetTouchableHandle();
    G4int PDGID = step->GetTrack()->GetDynamicParticle()->GetPDGcode();

    G4double edep = step->GetTotalEnergyDeposit();

    if (edep == 0.)
        return false;

    TPCHit* aHit = new TPCHit();
    aHit->SetTrackID(step->GetTrack()->GetTrackID());
    aHit->SetPos(step->GetPostStepPoint()->GetPosition());
    aHit->SetEdep(edep);
    aHit->SetPDGID(PDGID);  // Particle Data Group

    hitCollection->insert(aHit);
    return true;
}

void MySensitiveDetector::EndOfEvent(G4HCofThisEvent*)
{
    std::size_t nofHits = hitCollection->entries();
    G4cout << G4endl << "-------->Hits Collection: in this event they are "
           << nofHits << " hits in the TPC: " << G4endl;
    for (std::size_t i = 0; i < nofHits; i++)
        (*hitCollection)[i]->Print();
}
