//
// ********************************************************************
// * License and Disclaimer                                           *
// *                                                                  *
// * The  Geant4 software  is  copyright of the Copyright Holders  of *
// * the Geant4 Collaboration.  It is provided  under  the terms  and *
// * conditions of the Geant4 Software License,  included in the file *
// * LICENSE and available at  http://cern.ch/geant4/license .  These *
// * include a list of copyright holders.                             *
// *                                                                  *
// * Neither the authors of this software system, nor their employing *
// * institutes,nor the agencies providing financial support for this *
// * work  make  any representation or  warranty, express or implied, *
// * regarding  this  software system or assume any liability for its *
// * use.  Please see the license in the file  LICENSE  and URL above *
// * for the full disclaimer and the limitation of liability.         *
// *                                                                  *
// * This  code  implementation is the result of  the  scientific and *
// * technical work of the GEANT4 collaboration.                      *
// * By using,  copying,  modifying or  distributing the software (or *
// * any work based  on the software)  you  agree  to acknowledge its *
// * use  in  resulting  scientific  publications,  and indicate your *
// * acceptance of all terms of the Geant4 Software license.          *
// ********************************************************************
//
//
/// \file B1/src/EventAction.cc
/// \brief Implementation of the B1::EventAction class

#include "EventAction.hh"

#include "RunAction.hh"

namespace B1
{

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

EventAction::EventAction(RunAction* runAction) {}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void EventAction::BeginOfEventAction(G4Event const*) {}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void EventAction::EndOfEventAction(G4Event const* event)
{
    // get Hit Collection Container:
    G4HCofThisEvent* hce = event->GetHCofThisEvent();
    if (!hce)
        return;

    // get the Collection ID
    static G4int hcID
        = G4SDManager::GetSDMpointer()->GetCollectionID("SD/TPCHitCollection");
    // Cast the collection to your specific hit type
    auto hitsCollection = static_cast<TPCHitCollection*>(hce->GetHC(hcID));

    G4int n_vertex = event->GetNumberOfPrimaryVertex();
    for (G4int i = 0; i < n_vertex; i++)
    {
        G4PrimaryVertex* primaryVertex = event->GetPrimaryVertex(i);
        // Get the primary particle
        G4PrimaryParticle* primaryParticle = primaryVertex->GetPrimary();
        if (primaryParticle)
        {
            if (hitsCollection)
            {
                G4int eventID = event->GetEventID();
                size_t nHits = hitsCollection->entries();
                auto analysisManager = G4AnalysisManager::Instance();

                // loop
                for (size_t i = 0; i < nHits; i++)
                {
                    TPCHit* hit = (*hitsCollection)[i];

                    G4int pdgID = hit->GetPDGID();

                    if (std::abs(pdgID) == 13 || pdgID == 2212)
                    {
                        analysisManager->FillNtupleIColumn(0, 0, eventID);
                        analysisManager->FillNtupleDColumn(
                            0, 1, hit->GetEdep());
                        analysisManager->FillNtupleDColumn(
                            0, 2, hit->GetPos().x());
                        analysisManager->FillNtupleDColumn(
                            0, 3, hit->GetPos().y());
                        analysisManager->FillNtupleDColumn(
                            0, 4, hit->GetPos().z());

                        analysisManager->AddNtupleRow(0);
                    }
                }
                analysisManager->FillNtupleIColumn(1, 0, eventID);
                analysisManager->FillNtupleDColumn(1, 1, GetExitKE());
                analysisManager->FillNtupleDColumn(1, 2, GetExitMom().x());
                analysisManager->FillNtupleDColumn(1, 3, GetExitMom().y());
                analysisManager->FillNtupleDColumn(1, 4, GetExitMom().z());
                analysisManager->FillNtupleDColumn(1, 5, GetExitPos().x());
                analysisManager->FillNtupleDColumn(1, 6, GetExitPos().y());
                analysisManager->FillNtupleDColumn(1, 7, GetExitPos().z());

                analysisManager->AddNtupleRow(1);
            }
        }
    }
}
//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

}  // namespace B1
