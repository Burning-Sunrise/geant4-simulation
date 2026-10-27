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
/// \file B1/include/EventAction.hh
/// \brief Definition of the B1::EventAction class

#include "G4AnalysisManager.hh"
#include "G4Event.hh"
#include "G4HCofThisEvent.hh"
#include "G4MuonMinus.hh"
#include "G4ParticleDefinition.hh"
#include "G4PrimaryParticle.hh"
#include "G4PrimaryVertex.hh"
#include "G4SDManager.hh"
#include "G4UserEventAction.hh"
#include "MySensitiveDetector.hh"
#include "globals.hh"

#ifndef B1EventAction_h
#    define B1EventAction_h

class G4Event;

namespace B1
{

class RunAction;

/// Event action class

class EventAction : public G4UserEventAction
{
  public:
    EventAction(RunAction* runAction);
    ~EventAction() override = default;

    void BeginOfEventAction(G4Event const* event) override;
    void EndOfEventAction(G4Event const* event) override;

    void SetEntryPos(G4ThreeVector pos) { fEntryPos = pos; }
    G4ThreeVector GetEntryPos() const { return fEntryPos; }

    void SetEntryMom(G4ThreeVector mom) { fEntryMom = mom; }
    G4ThreeVector GetEntryMom() const { return fEntryMom; }

    void SetEntryKE(G4double ke) { fEntryKE = ke; }
    G4double GetEntryKE() const { return fEntryKE; }

    void SetEntered(G4bool entered) { fEntered = entered; }
    G4bool GetEntered() const { return fEntered; }

    void SetExitPos(G4ThreeVector pos) { fPos = pos; }
    G4ThreeVector GetExitPos() { return fPos; }

    void SetExitMom(G4ThreeVector mom) { fMom = mom; }
    G4ThreeVector GetExitMom() { return fMom; }

    void SetExitKE(G4double ke) { fKE = ke; }
    G4double GetExitKE() { return fKE; }

    void SetExited(G4bool exited) { fExited = exited; }
    G4bool GetExited() const { return fExited; }

    void AddGasStep(G4double stepLength)
    {
        fGasTrackLength += stepLength;
        ++fGasStepCount;
    }
    G4double GetGasTrackLength() const { return fGasTrackLength; }
    G4int GetGasStepCount() const { return fGasStepCount; }

  private:
    RunAction* fRunAction = nullptr;
    G4ThreeVector fEntryPos;
    G4ThreeVector fEntryMom;
    G4double fEntryKE = 0.;
    G4bool fEntered = false;
    G4ThreeVector fPos;
    G4ThreeVector fMom;
    G4double fKE = 0.;
    G4bool fExited = false;
    G4double fGasTrackLength = 0.;
    G4int fGasStepCount = 0;
};

}  // namespace B1

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

#endif
